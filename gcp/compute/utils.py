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
from copy import deepcopy
from functools import wraps

from cloudify import ctx
from cloudify.exceptions import NonRecoverableError

from gcp.gcp import GCPError, GCPHttpError
from gcp.gcp import is_missing_resource_error, is_resource_used_error
from gcp.compute import constants


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


def create_resource(func):
    def _decorator(resource, *args, **kwargs):
        if should_use_external_resource():
            try:
                resource.get()
            except GCPHttpError as error:
                if is_missing_resource_error(error):
                    name = ctx.node.properties.get(constants.RESOURCE_ID)
                    raise NonRecoverableError(
                        'Resource {} defined as external, but does not exist.'.
                        format(name))
                else:
                    raise error
        else:
            return func(resource, *args, **kwargs)

    return wraps(func)(_decorator)


def retry_on_failure(msg, delay=constants.RETRY_DEFAULT_DELAY):
    def _retry_on_failure(func):
        def _decorator(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except GCPHttpError as error:
                if is_resource_used_error(error):
                    ctx.operation.retry(msg, delay)
                else:
                    raise error

        return wraps(func)(_decorator)

    return _retry_on_failure


def get_firewall_rule_name(network, firewall):
    """
    Prefix firewall rule name with network name

    :param network: network to which the firewall rule belongs
    :param firewall: firewall for which the name is created
    :return: network prefixed firewall rule name
    """
    name = '{0}-{1}'.format(network, firewall)
    return get_gcp_resource_name(name)


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
        return gcp_config_from_properties
    else:
        gcp_config = ctx.provider_context['resources'][constants.GCP_CONFIG]
        return deepcopy(gcp_config)


def get_manager_provider_config():
    provider_config = ctx.provider_context.get('resources', {})
    agents_security_group = provider_config.get('agents_security_group', {})
    manager_agent_security_group = \
        provider_config.get('manager_agent_security_group', {})
    provider_context = {
        'agents_security_group': agents_security_group,
        'manager_security_group': manager_agent_security_group
    }
    return provider_context


def create_firewall_structure_from_rules(network, rules):
    firewall = {'name': get_firewall_rule_name(network, ctx.instance.id),
                'allowed': [],
                constants.SOURCE_TAGS: [],
                'sourceRanges': [],
                constants.TARGET_TAGS: []}

    for rule in rules:
        source_tags = rule.get('source_tags', [])
        target_tags = rule.get('target_tags', [])
        for tag in source_tags:
            tag = get_gcp_resource_name(tag)
            if tag not in firewall[constants.SOURCE_TAGS]:
                firewall[constants.SOURCE_TAGS].append(tag)
        for tag in target_tags:
            tag = get_gcp_resource_name(tag)
            if tag not in firewall[constants.TARGET_TAGS]:
                firewall[constants.TARGET_TAGS].append(tag)
        firewall['allowed'].extend([{'IPProtocol': rule.get('ip_protocol'),
                                    'ports': [rule.get('port', [])]}])
        cidr = rule.get('cidr_ip')
        if cidr and cidr not in firewall['sourceRanges']:
            firewall['sourceRanges'].append(cidr)
    return firewall


def get_key_user_string(user, key):
    return '{0}:{1}'.format(user, key)


def get_agent_ssh_key_string():
    key = ctx.provider_context['resources']['cloudify-agent']['public-key']
    user = ctx.provider_context['cloudify']['cloudify-agent']['user']
    return get_key_user_string(user, key)