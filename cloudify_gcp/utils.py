########
# Copyright (c) 2014-2020 Cloudify Platform Ltd. All rights reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import re
import sys
import time
import json
from functools import wraps
from abc import abstractmethod
from jsonschema import validate
from subprocess import check_output
from os.path import basename, expanduser

from six.moves import http_client

import yaml
from proxy_tools import Proxy
from googleapiclient.errors import HttpError

from cloudify import ctx
from cloudify.context import CloudifyContext
from cloudify.exceptions import NonRecoverableError, RecoverableError
from cloudify.utils import exception_to_error_cause

from ._compat import text_type, ABC
from . import constants
from .gcp import (
    GCPError,
    GoogleCloudPlatform,
    check_response,
    is_missing_resource_error,
    is_resource_used_error,
)


try:
    from cloudify.constants import (
        RELATIONSHIP_INSTANCE, NODE_INSTANCE)
except ImportError:
    NODE_INSTANCE = 'node-instance'
    RELATIONSHIP_INSTANCE = 'relationship-instance'


def generate_traceback_exception():
    _, exc_value, exc_traceback = sys.exc_info()
    response = exception_to_error_cause(exc_value, exc_traceback)
    return response


def camel_farm(identifier):
    """
    Convert from underscored to camelCase.
    """
    words = identifier.split('_')
    return ''.join([words[0]] + [word.capitalize() for word in words[1:]])


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
    # remove dash at the end
    while len(final_name) and final_name[-1] == "-":
        final_name = final_name[:-1]
    # convert string to lowercase
    final_name = final_name.lower()
    return final_name


def should_use_external_resource(ctx):
    return ctx.node.properties.get(constants.USE_EXTERNAL_RESOURCE, False)


def set_resource_id_if_use_external(resource_id):
    if should_use_external_resource(ctx) \
            and constants.RESOURCE_ID not in ctx.instance.runtime_properties:
        ctx.instance.runtime_properties[constants.RESOURCE_ID] = resource_id


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
        if should_use_external_resource(ctx):
            if not ctx.instance.runtime_properties.get(constants.RESOURCE_ID):
                resource_id = ctx.node.properties.get(constants.RESOURCE_ID)
                name = ctx.node.properties.get('name')
                if resource_id and name and resource_id != name:
                    raise NonRecoverableError(
                        'resource id can\'t have different value than '
                        'name {}!={}'.format(resource_id, name))
                if not resource_id and name:
                    resource_id = name

                if not resource_id:
                    raise NonRecoverableError('Resource id is missing.')

                ctx.instance.runtime_properties[
                    constants.RESOURCE_ID] = resource_id

            try:
                resource.body = resource.get()
            except HttpError as error:
                ctx.logger.error(str(error))
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


def runtime_properties_cleanup(ctx):
    # cleanup runtime properties
    # need to convert generaton to list, python 3
    # ctx.instance.runtime_properties is a dictionary, iterating over keys.
    keys = [key for key in ctx.instance.runtime_properties]
    for key in keys:
        del ctx.instance.runtime_properties[key]


def delete_if_not_external(resource):
    if not should_use_external_resource(ctx):
        try:
            return resource.delete()
        except HttpError as error:
            if is_missing_resource_error(error):
                ctx.logger.info('Resource already deleted.')
            else:
                raise error
    else:
        runtime_properties_cleanup(ctx)


def resource_created(ctx, resource_field):
    # resource_id is provided and all operations are finished
    if ctx.instance.runtime_properties.get(resource_field) and not \
            ctx.instance.runtime_properties.get('_operation'):
        ctx.logger.info('Resource already created.')
        return True
    return False


def resource_started(ctx, resource):
    resource_status = resource.get().get('status')

    if resource_status == constants.KUBERNETES_RUNNING_STATUS:
        ctx.logger.debug('Kubernetes resource running.')

    elif resource_status == constants.KUBERNETES_READY_STATUS:
        ctx.logger.debug('Kubernetes resource ready.')

    elif resource_status == constants.KUBERNETES_RECONCILING_STATUS:
        ctx.logger.debug('Kubernetes resource reconciling.')

    elif resource_status == constants.KUBERNETES_PROVISIONING_STATUS:
        ctx.operation.retry(
            'Kubernetes resource is still provisioning.', 15)

    elif resource_status == constants.KUBERNETES_ERROR_STATUS:
        raise NonRecoverableError('Kubernetes resource in error state.')

    else:
        ctx.logger.warn(
            'cluster resource is neither {0}, {1}, {2}.'
            ' Unknown Status: {3}'.format(
                constants.KUBERNETES_RUNNING_STATUS,
                constants.KUBERNETES_PROVISIONING_STATUS,
                constants.KUBERNETES_ERROR_STATUS, resource_status))


def resource_deleted(ctx, resource):
    if should_use_external_resource(ctx):
        ctx.logger.info('Used external resource.')
        return

    try:
        resource_status = resource.get().get('status')
    except HttpError as e:
        if e.resp.status == http_client.NOT_FOUND:
            resource_status = None
        else:
            raise e

    if not resource_status:
        ctx.logger.debug('Kubernetes resource deleted.')

    elif resource_status == constants.KUBERNETES_STOPPING_STATUS:
        ctx.operation.retry(
            'Kubernetes resource is still de-provisioning')

    elif resource_status == constants.KUBERNETES_RUNNING_STATUS:
        ctx.operation.retry(
            'Kubernetes resource is still running')

    elif resource_status == constants.KUBERNETES_READY_STATUS:
        ctx.operation.retry(
            'Kubernetes resource is still ready')

    elif resource_status == constants.KUBERNETES_ERROR_STATUS:
        raise NonRecoverableError(
            'Kubernetes resource failed to delete.')


def sync_operation(func):
    def _decorator(resource, *args, **kwargs):
        response = func(resource, *args, **kwargs)
        operation = response_to_operation(
            response, resource.config, resource.logger)
        while not operation.has_finished():
            time.sleep(1)
        return operation.last_response

    return wraps(func)(_decorator)


def async_operation(get=False):
    """
    Decorator for node methods which return an Operation
    Handles the operation if it exists

    :param get: if True, update runtime_properties with the result of
                self.get() when the Operation is complete
    """
    def decorator(func):
        def wrapper(self, *args, **kwargs):
            props = ctx.instance.runtime_properties
            response = props.get('_operation')

            if response:
                operation = response_to_operation(
                        response,
                        get_gcp_config(),
                        ctx.logger)

                try:
                    has_finished = operation.has_finished()
                except GCPError:
                    # If the operation has an error, clear it from
                    # runtime_properties so the next try will start from
                    # scratch.
                    props.pop('_operation')
                    raise

                if has_finished:
                    for key in '_operation', 'selfLink':
                        props.pop(key, None)
                    if get:
                        props.update(self.get())
                else:
                    ctx.operation.retry(
                        'Operation not completed yet: {}'.format(
                            operation.last_response['status']),
                        constants.RETRY_DEFAULT_DELAY)

            else:
                # Actually run the method
                response = func(self, *args, **kwargs)
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
                ctx.logger.error('Error Message {0}'.format(error.resp))
                if is_resource_used_error(error):
                    ctx.operation.retry(msg, delay)
                else:
                    raise error

        return wraps(func)(_decorator)

    return _retry_on_failure


def throw_cloudify_exceptions(func):
    def _decorator(*args, **kwargs):
        try:
            func_ctx = kwargs.get('ctx', ctx)
            result = func(*args, **kwargs)
            current_action = func_ctx.operation.name

            # in delete action
            if current_action != constants.DELETE_NODE_ACTION:
                return result

            # not finished gcp operation
            if func_ctx.instance.runtime_properties.get('_operation'):
                return result

            # called cloudify retry operation
            if func_ctx.operation._operation_retry:
                return result

            # cleanup runtime
            func_ctx.logger.info('Cleanup resource.')
            runtime_properties_cleanup(func_ctx)

            # return result
            return result
        except (RecoverableError, NonRecoverableError) as e:
            raise e
        except GCPError as e:
            func_ctx.logger.error('Error Message {0}'.format(str(e)))
            raise NonRecoverableError(str(e))

        except Exception as error:
            response = generate_traceback_exception()

            func_ctx.logger.error(
                'Error traceback {0} with message {1}'.format(
                    response['traceback'], response['message']))

            func_ctx.logger.error('Error Message {0}'.format(error))
            raise NonRecoverableError(str(error))

    return wraps(func)(_decorator)


def get_node(_ctx, target=False):
    if _ctx.type == RELATIONSHIP_INSTANCE:
        if target:
            return _ctx.target.node
        return _ctx.source.node
    else:  # _ctx.type == NODE_INSTANCE
        return _ctx.node


def get_gcp_config(node=None, requested_zone=None):

    node = node or get_node(ctx)

    def _get_gcp_config_from_properties():
        for config_key in [constants.GCP_CONFIG,
                           constants.GCP_CONFIG_OLD]:
            if config_key == constants.GCP_CONFIG_OLD:
                ctx.logger.warn(
                    'The client configuration key gcp_config is '
                    'deprecated and will be removed in a future '
                    'version of the plugin. '
                    'Please use client_config instead.')
            config = node.properties.get(config_key)
            if config:
                return config
        raise NonRecoverableError(
            'No valid client configuration key was found in node or '
            'source node properties. Valid keys: [client_config]')

    gcp_config = {}
    gcp_config.update(getattr(ctx.plugin, 'properties', {}))
    gcp_config_from_properties = _get_gcp_config_from_properties()

    if gcp_config_from_properties:
        gcp_config.update(gcp_config_from_properties)

    if not gcp_config:
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
    if 'auth' not in gcp_config:
        raise NonRecoverableError("No auth provided in gcp_config.")
    # if auth is a string so its a service account json
    if isinstance(gcp_config['auth'], text_type):
        try:
            gcp_config['auth'] = get_gcp_config_dict(gcp_config['auth'])
            # add on the fly the 'project' input
            gcp_config['project'] = gcp_config['auth']['project_id']
        except Exception as e:
            raise NonRecoverableError("invalid gcp_config provided: {}"
                                      .format(e))

    if gcp_config['auth'].get('private_key'):
        gcp_config['auth']['private_key'] = gcp_config['auth'][
            'private_key'].replace('\\n', '\n')

    if 'refresh_token' in gcp_config['auth']:
        # admin config
        try:
            for key in ('client_id', 'client_secret', 'refresh_token'):
                gcp_config['auth'][key]
        except Exception as e:
            raise NonRecoverableError("invalid gcp_config provided: {}"
                                      .format(e))
    else:
        # Validate the config contains what it should
        try:
            for key in ('project', 'auth', 'zone'):
                gcp_config[key]
        except Exception as e:
            raise NonRecoverableError("invalid gcp_config provided: {}"
                                      .format(e))
        # If no network is specified, assume the GCP default network, 'default'
        gcp_config.setdefault('network', 'default')
        if not requested_zone:
            return update_zone(gcp_config)
        else:
            gcp_config['zone'] = requested_zone
    return gcp_config


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

    try:
        public_key = check_output([
            'ssh-keygen', '-y',  # generate public key from private key
            '-P', '',  # don't prompt for passphrase (would hang forever)
            '-f', expanduser(cloudify_agent['agent_key_path'])])
    except Exception as e:
        # any failure here is fatal
        raise NonRecoverableError('key generation failure', e)
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


class Operation(GoogleCloudPlatform, ABC):

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
    def _get(self):
        pass


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
        filter_resource_types=None):
    """
    Get all relationships of a particular node or the current context.

    Optionally filter based on relationship type, node type.
    """
    filter_relationships = filter_relationships or []
    filter_resource_types = filter_resource_types or []

    if isinstance(relationships, (CloudifyContext, Proxy)):
        # Shortcut to support supplying ctx directly
        relationships = relationships.instance.relationships
    # And coerce the other inputs to lists if they are strings:
    if isinstance(filter_resource_types, (text_type, bytes)):
        filter_resource_types = [filter_resource_types]
    if isinstance(filter_relationships, (text_type, bytes)):
        filter_relationships = [filter_relationships]
    results = []
    for rel in relationships:
        res_type = get_resource_type(rel.target)
        if not any([
            # if the instance runtime_properties doesn't have a 'kind' key
            # filter it out regardless as it's not a GCP node.
            not res_type,
            # filter on the GCP type ('kind' attribute)
            filter_resource_types and res_type not in filter_resource_types,
            # Filter by relationship type
            filter_relationships and rel.type not in filter_relationships
        ]):
            results.append(rel)
    return results


def get_network_node(ctx):
    for kind in 'compute#subnetwork', 'compute#network':
        network_list = get_relationships(
                ctx,
                filter_resource_types=[kind],
                )
        if len(network_list) > 1:
            raise NonRecoverableError(
                    'Only one {} is supported at a time'.format(kind))
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
        if get_resource_type(net_node) == 'compute#network':
            network = net_node.instance.runtime_properties['selfLink']
        elif get_resource_type(net_node) == 'compute#subnetwork':
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


def get_gcp_config_dict(gcp_config_string):
    gcp_json = json.loads(gcp_config_string)
    validate(instance=gcp_json, schema=constants.GCP_CREDENTIALS_SCHEMA)
    return gcp_json
