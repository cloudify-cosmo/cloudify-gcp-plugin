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
from plugin.gcp.keypair import KeyPair

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
def create_instance(gcp_config, instance_type, image_id, properties, **kwargs):
    gcp_config['network'] = utils.get_gcp_resource_name(gcp_config['network'])
    script = properties.get('startup_script')
    if script:
        script = ctx.download_resource(script)
    instance = Instance(gcp_config,
                        ctx.logger,
                        instance_name=ctx.instance.id,
                        image=image_id,
                        machine_type=instance_type,
                        external_ip=properties.get('externalIP', False),
                        startup_script=script)
    instance.create()
    ctx.instance.runtime_properties[NAME] = instance.name
    set_ip(instance)


@operation
@throw_cloudify_exceptions
def add_instance_tag(gcp_config, instance_name, tag, **kwargs):
    gcp_config['network'] = utils.get_gcp_resource_name(gcp_config['network'])
    instance = Instance(gcp_config,
                        ctx.logger,
                        instance_name=instance_name)
    instance.set_tags([utils.get_gcp_resource_name(tag)])


@operation
@throw_cloudify_exceptions
def remove_instance_tag(gcp_config, instance_name, tag, **kwargs):
    if not instance_name:
        return
    gcp_config['network'] = utils.get_gcp_resource_name(gcp_config['network'])
    instance = Instance(gcp_config,
                        ctx.logger,
                        instance_name=instance_name)
    instance.remove_tags([utils.get_gcp_resource_name(tag)])


@operation
@throw_cloudify_exceptions
def add_external_ip(gcp_config, instance_name, **kwargs):
    # check if the instance has no external ips, only one is supported so far
    gcp_config['network'] = utils.get_gcp_resource_name(gcp_config['network'])
    instance = Instance(gcp_config,
                        ctx.logger,
                        instance_name=instance_name)
    instance.add_access_config()
    set_ip(instance, relationship=True)


@operation
@throw_cloudify_exceptions
def remove_external_ip(gcp_config, instance_name, **kwargs):
    if not instance_name:
        return
    gcp_config['network'] = utils.get_gcp_resource_name(gcp_config['network'])
    instance = Instance(gcp_config,
                        ctx.logger,
                        instance_name=instance_name)
    instance.delete_access_config()


@operation
@throw_cloudify_exceptions
def delete_instance(gcp_config, **kwargs):
    name = ctx.instance.runtime_properties.get(NAME)
    if not name:
        return
    instance = Instance(gcp_config,
                        ctx.logger,
                        instance_name=name)
    instance.delete()
    if ctx.instance.runtime_properties.get(NAME):
        ctx.instance.runtime_properties.pop(NAME)


@operation
@throw_cloudify_exceptions
def create_network(gcp_config, network, **kwargs):
    network['name'] = utils.get_gcp_resource_name(network['name'])
    network = Network(gcp_config,
                      ctx.logger,
                      network=network)
    network.create()
    ctx.instance.runtime_properties[NAME] = network.name


@operation
@throw_cloudify_exceptions
def delete_network(gcp_config, **kwargs):
    network_name = ctx.instance.runtime_properties.get(NAME)
    if not network_name:
        return
    network = Network(gcp_config,
                      ctx.logger,
                      network=network_name)

    network.delete()
    if ctx.instance.runtime_properties.get(NAME):
        ctx.instance.runtime_properties.pop(NAME)


@operation
@throw_cloudify_exceptions
def create_firewall_rule(gcp_config, firewall_rule, **kwargs):
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
    firewall_name = ctx.instance.runtime_properties.get(NAME)
    if not firewall_name:
        return
    network_name = utils.get_gcp_resource_name(gcp_config['network'])
    firewall = {'name': firewall_name}
    firewall = FirewallRule(gcp_config,
                            ctx.logger,
                            firewall=firewall,
                            network=network_name)
    firewall.delete()
    if ctx.instance.runtime_properties.get(NAME):
        ctx.instance.runtime_properties.pop(NAME)


@operation
@throw_cloudify_exceptions
def create_security_group(gcp_config, rules, **kwargs):
    firewall = create_firewall_structure_from_rules(gcp_config['network'],
                                                    rules)
    firewall = FirewallRule(gcp_config,
                            ctx.logger,
                            firewall,
                            gcp_config['network'])
    firewall.create()
    ctx.instance.runtime_properties[NAME] = firewall.name


@operation
@throw_cloudify_exceptions
def create_keypair(gcp_config, user, private_key_path, **kwargs):
    keypair = KeyPair(gcp_config,
                      ctx.logger,
                      user,
                      private_key_path)
    keypair.create_keypair()
    keypair.add_project_ssh_key(user, keypair.public_key)
    ctx.instance.runtime_properties['gcp_private_key'] = keypair.private_key
    ctx.instance.runtime_properties['gcp_public_key'] = keypair.public_key
    keypair.save_private_key()


@operation
@throw_cloudify_exceptions
def save_private_key(gcp_config,
                     private_key,
                     user,
                     private_key_path,
                     **kwargs):
    keypair = KeyPair(gcp_config,
                      ctx.logger,
                      user,
                      private_key_path)
    keypair.private_key = private_key
    keypair.save_private_key()


@operation
@throw_cloudify_exceptions
def delete_private_key(gcp_config, user, private_key_path, **kwargs):
    keypair = KeyPair(gcp_config,
                      ctx.logger,
                      user,
                      private_key_path)
    keypair.remove_private_key()


@operation
@throw_cloudify_exceptions
def delete_keypair(gcp_config, user, private_key_path, **kwargs):
    keypair = KeyPair(gcp_config,
                      ctx.logger,
                      user,
                      private_key_path)
    keypair.public_key = ctx.instance.runtime_properties['gcp_public_key']
    keypair.remove_project_ssh_key()
    ctx.instance.runtime_properties.pop('gcp_public_key')
    ctx.instance.runtime_properties.pop('gcp_private_key')


def set_ip(instance, relationship=False):
    instances = instance.list()
    item = utils.get_item_from_gcp_response('name', instance.name, instances)
    if relationship:
        ctx.target.instance.runtime_properties['gcp_resource_id'] = \
            item['networkInterfaces'][0]['accessConfigs'][0]['natIP']
    else:
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
