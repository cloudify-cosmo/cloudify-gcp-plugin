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
from cloudify.decorators import operation
from cloudify.exceptions import NonRecoverableError

from plugin.gcp.service import GCPError
from plugin.gcp import utils
from plugin.gcp.firewall import FirewallRule
from plugin.gcp.instance import Instance
from plugin.gcp.network import Network
from plugin import tags

NAME = 'gcp_name'


def throw_cloudify_exceptions(func):
    def _decorator(*args, **kwargs):
        try:
            func(*args, **kwargs)
        except GCPError as e:
            raise NonRecoverableError(e.message)
    return wraps(func)(_decorator)


@operation
@throw_cloudify_exceptions
def create_instance(gcp_config, instance, **kwargs):
    ctx.logger.info('Create instance')
    gcp_config['network'] = utils.get_gcp_resource_name(gcp_config['network'])
    tag_list = instance.get('tags', []).extend(tags.AGENT_TAG)
    script = instance.get('startup_script')
    if script:
        script = ctx.download_resource(script)
    instance = Instance(gcp_config,
                        ctx.logger,
                        instance_name=ctx.instance.id,
                        image=instance['image'],
                        tags=tag_list,
                        externalIP=instance.get('externalIP', False),
                        startup_script=script)
    instance.create()
    ctx.instance.runtime_properties[NAME] = instance.name
    set_ip(instance)


@operation
@throw_cloudify_exceptions
def delete_instance(gcp_config, **kwargs):
    ctx.logger.info('Delete instance')
    name = ctx.instance.runtime_properties[NAME]
    instance = Instance(gcp_config,
                        ctx.logger,
                        instance_name=name)
    instance.delete()
    ctx.instance.runtime_properties.pop(NAME)


@operation
@throw_cloudify_exceptions
def create_network(gcp_config, network, **kwargs):
    ctx.logger.info('Create network')
    network['name'] = utils.get_gcp_resource_name(network['name'])
    network = Network(gcp_config,
                      ctx.logger,
                      network=network)
    network.create()
    ctx.instance.runtime_properties[NAME] = network['name']


@operation
@throw_cloudify_exceptions
def delete_network(gcp_config, **kwargs):
    ctx.logger.info('Delete network')
    network_name = ctx.instance.runtime_properties[NAME]
    network = Network(gcp_config,
                      ctx.logger,
                      network=network_name)

    network.delete()
    ctx.instance.runtime_properties.pop(NAME)


@operation
@throw_cloudify_exceptions
def create_firewall_rule(gcp_config, firewall_rule, **kwargs):
    ctx.logger.info('Create firewall rule')
    network_name = utils.get_gcp_resource_name(gcp_config['network'])
    firewall_rule['name'] = utils.get_firewall_rule_name(network_name,
                                                         firewall_rule)
    firewall = FirewallRule(gcp_config,
                            ctx.logger,
                            firewall=firewall_rule,
                            network=network_name)

    firewall.create()
    ctx.instance.runtime_properties[NAME] = firewall.name


@operation
@throw_cloudify_exceptions
def delete_firewall_rule(gcp_config, **kwargs):
    ctx.logger.info('Delete firewall rule')
    network_name = utils.get_gcp_resource_name(gcp_config['network'])
    firewall = {'name': ctx.instance.runtime_properties[NAME]}
    firewall = FirewallRule(gcp_config,
                            ctx.logger,
                            firewall=firewall,
                            network=network_name)
    firewall.delete()
    ctx.instance.runtime_properties.pop(NAME)


@operation
@throw_cloudify_exceptions
def create_security_group(gcp_config, rules, **kwargs):
    ctx.logger.info('Create security group')
    firewall = create_firewall_structure_from_rules(gcp_config['network'],
                                                    rules)
    firewall = FirewallRule(gcp_config,
                            ctx.logger,
                            firewall,
                            gcp_config['network'])
    firewall.create()
    ctx.instance.runtime_properties[NAME] = firewall.name


def set_ip(instance):
    instances = instance.list()
    item = utils.get_item_from_gcp_response(
        'name',
        ctx.instance.runtime_properties[NAME],
        instances)
    ctx.instance.runtime_properties['ip'] = \
        item['networkInterfaces'][0]['networkIP']
    # only with one default network interface


def create_firewall_structure_from_rules(network, rules):
    firewall = {'name': utils.get_firewall_rule_name(network, ctx.instance.id),
                'allowed': [],
                'sourceTags': [],
                'sourceRanges': [],
                'targetTags': []}

    for rule in rules:
        firewall['sourceTags'].extend(rule.get('source_tags', []))
        firewall['allowed'].extend([{'IPProtocol': rule.get('ip_protocol'),
                                    'ports': rule.get('ports', [])}])
        firewall['sourceRanges'].extend(rule.get('cidr_ip', []))
        firewall['targetTags'].extend(rule.get('target_tags', []))
    return firewall
