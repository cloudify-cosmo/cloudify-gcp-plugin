########
# Copyright (c) 2014 GigaSpaces Technologies Ltd. All rights reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
#    * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    * See the License for the specific language governing permissions and
#    * limitations under the License.

import re
import string
import time
from functools import wraps
from subprocess import check_output
from os.path import basename, expanduser
from abc import ABCMeta, abstractmethod

import yaml
from proxy_tools import Proxy
from googleapiclient.errors import HttpError

from cloudify import ctx
from cloudify.context import CloudifyContext
from cloudify.exceptions import NonRecoverableError

from . import constants
from .gcp import (
    GCPError,
    GoogleCloudPlatform,
    check_response,
    is_missing_resource_error,
    is_resource_used_error,
    )


def camel_farm(identifier):
    """
    Convert from underscored to camelCase.
    """
    words = identifier.split('_')
    return ''.join([words[0]] + map(string.capitalize, words[1:]))


def get_item_from_gcp_response(key_field, key_name, items):
    """
    Get item from GCP REST response JSON list by name.
    items = [{ 'key_field': 'key_name', 'key_field_value': 'value'}]
    :param key_field: item dictionary key
    :param key_value: item dictionary value
    :param items: list of items(dictionaries)
    :return: item if found in collection, None otherwise
    """
    for item in items.get('items', []):
        if item.get(key_field) == key_name:
            return item
    return None


def get_gcp_resource_name(name):
    """
    Create GCP accepted name of resource. From GCP specification:
    "Specifically, the name must be 1-63 characters long and match the regular
    expression [a-z]([-a-z0-9]*[a-z0-9])? which means the first character must
    be a lowercase letter, and all following characters must be a dash,
    lowercase letter, or digit, except the last character,
    which cannot be a dash."
    :param name: name of resource to be given
    :return: GCP accepted instance name
    """
    # replace underscores with hyphens
    final_name = name.replace('_', '-')
    # remove all non-alphanumeric characters except hyphens
    final_name = re.sub(r'[^a-zA-Z0-9-]+', '', final_name)
    # assure the first character is alpha
    if not final_name[0].isalpha():
        final_name = '{0}{1}'.format('a', final_name)
    # trim to the length limit
    if len(final_name) > constants.MAX_GCP_NAME:
        remain_len = constants.MAX_GCP_NAME - len(final_name)
        final_name = '{0}{1}'.format(
            final_name[:remain_len - constants.ID_HASH_CONST],
            final_name[-constants.ID_HASH_CONST:])
    # convert string to lowercase
    return final_name.lower()


def should_use_external_resource():
    return ctx.node.properties.get(constants.USE_EXTERNAL_RESOURCE, False)


def assure_resource_id_correct():
    resource_id = ctx.node.properties.get(constants.RESOURCE_ID)
    if not resource_id:
        raise NonRecoverableError('Resource id is missing.')

    if resource_id != get_gcp_resource_name(resource_id):
        raise NonRecoverableError('{} cannot be used as resource id.'
                                  .format(resource_id))
    return resource_id


def get_final_resource_name(name):
    return name or get_gcp_resource_name(ctx.instance.id)


def create_resource(func):
    def _decorator(resource, *args, **kwargs):
        if should_use_external_resource():
            try:
                resource.body = resource.get()
            except HttpError as error:
                if is_missing_resource_error(error):
                    name = ctx.node.properties.get(constants.RESOURCE_ID)
                    raise NonRecoverableError(
                        'Resource {0} defined as external, '
                        'but does not exist. Error: {1}'.
                        format(name, str(error)))
                else:
                    raise error
            ctx.instance.runtime_properties.update(resource.body)
        else:
            return func(resource, *args, **kwargs)

    return wraps(func)(_decorator)


@create_resource
def create(resource):
    return resource.create()


def delete_if_not_external(resource):
    if not should_use_external_resource():
        return resource.delete()


def sync_operation(func):
    def _decorator(resource, *args, **kwargs):
        response = func(resource, *args, **kwargs)
        operation = response_to_operation(
            response, resource.config, resource.logger)
        while not operation.has_finished():
            time.sleep(1)
        return operation.last_response

    return wraps(func)(_decorator)


def async_operation(get=False, relationship=False):
    """
    Decorator for node methods which return an Operation
    Handles the operation if it exists

    :param get: if True, update runtime_properties with the result of
                self.get() when the Operation is complete
    :param relationship: if True, this method is called as part of a
                relationship operation (e.g. establish, unlink), and the
                operation data should be stored under
                runtime_properties['_operations'][target_id] to avoid
                collisions.
    (relationship = True implies get = False)
    """
    def decorator(func):
        def wrapper(self, *args, **kwargs):
            if relationship:
                props = ctx.source.instance.runtime_properties
                response = props.setdefault('_operations', {}).get(
                        ctx.target.instance.id)
            else:
                props = ctx.instance.runtime_properties
                response = props.get('_operation', None)

            props.dirty = True

            if response:
                operation = response_to_operation(
                        response,
                        get_gcp_config(),
                        ctx.logger)
                response = operation.get()

                if response['status'] in ('PENDING', 'RUNNING'):
                    ctx.operation.retry(
                        'Operation not completed yet: {}'.format(
                            response['status']),
                        constants.RETRY_DEFAULT_DELAY)
                elif response['status'] == 'DONE':
                    if relationship:
                        props['_operations'].pop(ctx.target.instance.id)
                    else:
                        for key in '_operation', 'name', 'selfLink':
                            props.pop(key, None)
                        if get:
                            props.update(self.get())
                else:
                    raise NonRecoverableError(
                            'Unknown status response from operation')

            else:
                # Actually run the method
                response = func(self, *args, **kwargs)
                if relationship:
                    props.setdefault('_operations', {})[
                            ctx.target.instance.id] = response
                else:
                    props['_operation'] = response

                ctx.operation.retry('Operation started')

        return wraps(func)(wrapper)
    return decorator


def retry_on_failure(msg, delay=constants.RETRY_DEFAULT_DELAY):
    def _retry_on_failure(func):
        def _decorator(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except HttpError as error:
                if is_resource_used_error(error):
                    ctx.operation.retry(msg, delay)
                else:
                    raise error

        return wraps(func)(_decorator)

    return _retry_on_failure


def throw_cloudify_exceptions(func):
    def _decorator(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except GCPError as e:
            raise NonRecoverableError(e.message)

    return wraps(func)(_decorator)


def get_gcp_config():
    def _get_gcp_config_from_properties():
        try:
            return ctx.node.properties[constants.GCP_CONFIG]
        except NonRecoverableError:
            return ctx.source.node.properties[constants.GCP_CONFIG]

    gcp_config_from_properties = _get_gcp_config_from_properties()
    if gcp_config_from_properties:
        gcp_config = gcp_config_from_properties
    else:
        try:
            with open(expanduser(constants.GCP_DEFAULT_CONFIG_PATH)) as f:
                gcp_config = yaml.load(f)
        except (IOError, OSError) as e:
            raise NonRecoverableError(
                '{} not provided as a property and the config file ({}) '
                'does not exist either: {}'.format(
                    constants.GCP_CONFIG,
                    constants.GCP_DEFAULT_CONFIG_PATH,
                    e,
                    ))

    # Validate the config contains what it should
    try:
        for key in 'project', 'auth', 'zone':
            gcp_config[key]
    except Exception as e:
        raise NonRecoverableError("invalid gcp_config provided: {}".format(e))

    # If no network is specified, assume the GCP default network, 'default'
    gcp_config.setdefault('network', 'default')

    return update_zone(gcp_config)


def update_zone(gcp_config):
    def _get_zone_from_runtime_properties():
        try:
            return ctx.instance.runtime_properties.get(constants.GCP_ZONE)
        except NonRecoverableError:
            src = ctx.source.instance.runtime_properties
            tar = ctx.target.instance.runtime_properties
            return src.get(constants.GCP_ZONE) or tar.get(constants.GCP_ZONE)

    non_default_zone = _get_zone_from_runtime_properties()
    if non_default_zone:
        gcp_config['zone'] = non_default_zone

    return gcp_config


def is_object_deleted(obj):
    try:
        obj.get()
    except HttpError as error:
        if is_missing_resource_error(error):
            return True
    return False


def get_key_user_string(user, public_key):
    cleaned_user = re.sub(r'\s+', ' ', user).strip()
    cleaned_public_key = re.sub(r'\s+', ' ', public_key).strip()

    if cleaned_public_key.count(' ') >= 1:
        keytype, key_blob = cleaned_public_key.split(' ')[:2]
    else:
        raise NonRecoverableError('Incorrect format of public key')
    protocol = '{0}:{1}'.format(cleaned_user, keytype)

    return '{0} {1} {2}'.format(protocol, key_blob, cleaned_user)


def get_agent_ssh_key_string():
    cloudify_agent = {}

    try:
        cloudify_agent.update(
                ctx.provider_context['cloudify']['cloudify_agent'])
    except KeyError:
        pass

    # node-specific overrides should take precendence
    # cloudify_agent is deprecated but may still be used.
    for key in 'cloudify_agent', 'agent_config':
        cloudify_agent.update(ctx.node.properties.get(key, {}))

    if 'agent_key_path' not in cloudify_agent:
        ctx.logger.debug('agent to be installed but key file info not found')
        return ''

    public_key = check_output([
        'ssh-keygen', '-y',  # generate public key from private key
        '-P', '',  # don't prompt for passphrase (would hang forever)
        '-f', expanduser(cloudify_agent['agent_key_path'])])
    # add the agent user to the key. GCP uses this to create user accounts on
    # the instance.
    full_key = '{user}:{key} {user}@cloudify'.format(
            key=public_key.strip(),
            user=cloudify_agent['user'])

    return full_key


def response_to_operation(response, config, logger):
    if 'zone' in response:
        return ZoneOperation(config, logger, response)
    elif 'region' in response:
        return RegionOperation(config, logger, response)
    else:
        return GlobalOperation(config, logger, response)


class Operation(GoogleCloudPlatform):
    __metaclass__ = ABCMeta

    def __init__(self, config, logger, response):
        super(Operation, self).__init__(config, logger, response['name'])
        for item in ('zone', 'region'):
            if item in response:
                setattr(self, item, response[item])
        self.last_response = None
        self.last_status = None

    def has_finished(self):
        if self.last_status != constants.GCP_OP_DONE:
            self.get()

        return self.last_status == constants.GCP_OP_DONE

    @check_response
    def get(self):
        self.last_response = self._get()
        self.last_status = self.last_response['status']
        return self.last_response

    @abstractmethod
    def _get(self): pass


class GlobalOperation(Operation):
    def _get(self):
        return self.discovery.globalOperations().get(
            project=self.project,
            operation=self.name).execute()


class RegionOperation(Operation):
    def _get(self):
        return self.discovery.regionOperations().get(
            project=self.project,
            region=basename(self.region),
            operation=self.name).execute()


class ZoneOperation(Operation):
    def _get(self):
        return self.discovery.zoneOperations().get(
            project=self.project,
            zone=basename(self.zone),
            operation=self.name).execute()


def get_relationships(
        relationships,
        filter_relationships=None,
        filter_nodes=None,
        filter_resource_types=None):
    """
    Get all relationships of a particular node or the current context.

    Optionally filter based on relationship type, node type.
    """
    if isinstance(relationships, (CloudifyContext, Proxy)):
        # Shortcut to support supplying ctx directly
        relationships = relationships.instance.relationships
    # And coerce the other inputs to lists if they are strings:
    if isinstance(filter_resource_types, basestring):
        filter_resource_types = [filter_resource_types]
    if isinstance(filter_relationships, basestring):
        filter_relationships = [filter_relationships]
    if isinstance(filter_nodes, basestring):
        filter_nodes = [filter_nodes]
    results = []
    for rel in relationships:
        res_type = get_resource_type(rel.target)
        if not any([
                # if the instance runtime_properties doesn't have a 'kind' key
                # filter it out regardless as it's not a GCP node.
                (not res_type),

                # filter on the GCP type ('kind' attribute)
                (filter_resource_types and
                 res_type not in filter_resource_types),

                # Filter by relationship type
                (filter_relationships and
                 rel.type not in filter_relationships),

                # filter by node type (doesn't work with derived types)
                (filter_nodes and
                 rel.target.node.type not in filter_nodes),
                ]):
            results.append(rel)
    return results


def get_network_node(ctx):
    network_list = get_relationships(
            ctx,
            filter_relationships='cloudify.gcp.relationships.'
                                 'contained_in_network',
            )
    if len(network_list) > 0:
        return network_list[0].target


def get_net_and_subnet(ctx):
    """
    Returns a tuple of the ctx node's
    (Network, Subnetwork)
    """
    net_node = get_network_node(ctx)

    subnetwork = None
    if net_node:
        if net_node.node.type == 'cloudify.gcp.nodes.Network':
            network = net_node.instance.runtime_properties['selfLink']
        elif net_node.node.type == 'cloudify.gcp.nodes.SubNetwork':
            network = net_node.instance.runtime_properties['network']
            subnetwork = net_node.instance.runtime_properties['selfLink']
        else:
            raise NonRecoverableError(
                'Unsupported target type for '
                "'cloudify.gcp.relationships.instance_contained_in_network")
    else:
        config = get_gcp_config()
        network = config['network']

        if network == 'default':
            network = 'global/networks/default'
        elif '/' not in network:
            network = 'projects/{0}/global/networks/{1}'.format(
                    config['project'], network)

    return network, subnetwork


def get_network(ctx):
    return get_net_and_subnet(ctx)[0]


def get_resource_type(ctx):
    return ctx.instance.runtime_properties.get('kind')
