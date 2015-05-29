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
from functools import wraps

from cloudify import ctx
from cloudify.exceptions import NonRecoverableError
from plugin.gcp.service import GCPError
from plugin.gcp import utils

NAME = 'gcp_name'
GCP_CONFIG = 'gcp_config'
ID = 'id'
SECURITY_GROUPS = ['management_security_group',
                   'manager_agent_security_group',
                   'agents_security_group']


def throw_cloudify_exceptions(func):
    def _decorator(*args, **kwargs):
        try:
            func(*args, **kwargs)
        except GCPError as e:
            raise NonRecoverableError(e.message)
    return wraps(func)(_decorator)


def get_manager_provider_config():
    provider_config = ctx.provider_context.get('resources', {})
    agents_security_group = provider_config.get('agents_security_group', {})
    manager_agent_security_group = \
        provider_config.get('manager_agent_security_group', {})
    provider_context = {
        'agents_security_group': agents_security_group.get(ID),
        'manager_security_group': manager_agent_security_group.get(ID)
    }
    return provider_context


def create_firewall_structure_from_rules(network, rules):
    firewall = {'name': utils.get_firewall_rule_name(network, ctx.instance.id),
                'allowed': [],
                'sourceTags': [],
                'sourceRanges': [],
                'targetTags': []}

    for rule in rules:
        source_tags = rule.get('source_tags', [])
        for tag in source_tags:
            tag = utils.get_gcp_resource_name(tag)
            if tag not in firewall['sourceTags']:
                firewall['sourceTags'].append(tag)
        firewall['allowed'].extend([{'IPProtocol': rule.get('ip_protocol'),
                                    'ports': [rule.get('port', [])]}])
        cidr = rule.get('cidr_ip')
        if cidr and cidr not in firewall['sourceRanges']:
            firewall['sourceRanges'].append(cidr)
        firewall['targetTags'].extend(rule.get('target_tags', []))
    ctx.logger.info(str(firewall))
    return firewall
