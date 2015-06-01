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

from cloudify import ctx
from cloudify.decorators import operation

from plugin import utils
from plugin.utils import throw_cloudify_exceptions
from plugin.gcp.utils import get_gcp_resource_name
from plugin.gcp.utils import get_firewall_rule_name
from plugin.gcp.utils import get_item_from_gcp_response
from plugin.gcp.firewall import FirewallRule
from plugin.gcp.instance import Instance
from plugin.gcp.network import Network
from plugin.gcp.keypair import KeyPair


@operation
@throw_cloudify_exceptions
def create_instance(gcp_config, instance_type, image_id, properties, **kwargs):
    gcp_config['network'] = get_gcp_resource_name(gcp_config['network'])
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
    if ctx.node.properties['install_agent']:
        add_to_security_groups(instance)
    ctx.logger.info(str(instance.to_dict()))
    instance.create()
    ctx.instance.runtime_properties[utils.NAME] = instance.name
    set_ip(instance)


@operation
@throw_cloudify_exceptions
def add_instance_tag(gcp_config, instance_name, tag, **kwargs):
    gcp_config['network'] = get_gcp_resource_name(gcp_config['network'])
    instance = Instance(gcp_config,
                        ctx.logger,
                        instance_name=instance_name)
    instance.set_tags([get_gcp_resource_name(t) for t in tag])


@operation
@throw_cloudify_exceptions
def remove_instance_tag(gcp_config, instance_name, tag, **kwargs):
    if not instance_name:
        return
    gcp_config['network'] = get_gcp_resource_name(gcp_config['network'])
    instance = Instance(gcp_config,
                        ctx.logger,
                        instance_name=instance_name)
    instance.remove_tags([get_gcp_resource_name(t) for t in tag])


@operation
@throw_cloudify_exceptions
def add_external_ip(gcp_config, instance_name, **kwargs):
    # check if the instance has no external ips, only one is supported so far
    gcp_config['network'] = get_gcp_resource_name(gcp_config['network'])
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
    gcp_config['network'] = get_gcp_resource_name(gcp_config['network'])
    instance = Instance(gcp_config,
                        ctx.logger,
                        instance_name=instance_name)
    instance.delete_access_config()


@operation
@throw_cloudify_exceptions
def delete_instance(gcp_config, **kwargs):
    name = ctx.instance.runtime_properties.get(utils.NAME)
    if not name:
        return
    instance = Instance(gcp_config,
                        ctx.logger,
                        instance_name=name)
    instance.delete()
    if ctx.instance.runtime_properties.get(utils.NAME):
        ctx.instance.runtime_properties.pop(utils.NAME)


@operation
@throw_cloudify_exceptions
def create_network(gcp_config, network, **kwargs):
    network['name'] = get_gcp_resource_name(network['name'])
    network = Network(gcp_config,
                      ctx.logger,
                      network=network)
    network.create()
    ctx.instance.runtime_properties[utils.NAME] = network.name


@operation
@throw_cloudify_exceptions
def delete_network(gcp_config, **kwargs):
    network = {'name': ctx.instance.runtime_properties.get(utils.NAME)}
    if not network['name']:
        return
    network = Network(gcp_config,
                      ctx.logger,
                      network=network)

    network.delete()
    if ctx.instance.runtime_properties.get(utils.NAME):
        ctx.instance.runtime_properties.pop(utils.NAME)


@operation
@throw_cloudify_exceptions
def create_firewall_rule(gcp_config, firewall_rule, **kwargs):
    network_name = get_gcp_resource_name(gcp_config['network'])
    firewall_rule['name'] = get_firewall_rule_name(network_name,
                                                   firewall_rule)
    firewall = FirewallRule(gcp_config,
                            ctx.logger,
                            firewall=firewall_rule,
                            network=network_name)

    firewall.create()
    ctx.instance.runtime_properties[utils.NAME] = firewall.name


@operation
@throw_cloudify_exceptions
def delete_firewall_rule(gcp_config, **kwargs):
    firewall_name = ctx.instance.runtime_properties.get(utils.NAME)
    if not firewall_name:
        return
    network_name = get_gcp_resource_name(gcp_config['network'])
    firewall = {'name': firewall_name}
    firewall = FirewallRule(gcp_config,
                            ctx.logger,
                            firewall=firewall,
                            network=network_name)
    firewall.delete()
    if ctx.instance.runtime_properties.get(utils.NAME):
        ctx.instance.runtime_properties.pop(utils.NAME)


@operation
@throw_cloudify_exceptions
def create_security_group(gcp_config, rules, **kwargs):
    firewall = utils.create_firewall_structure_from_rules(
        gcp_config['network'],
        rules)
    ctx.instance.runtime_properties[utils.TARGET_TAGS] = \
        firewall[utils.TARGET_TAGS]
    ctx.instance.runtime_properties[utils.SOURCE_TAGS] = \
        firewall[utils.SOURCE_TAGS]
    firewall = FirewallRule(gcp_config,
                            ctx.logger,
                            firewall,
                            gcp_config['network'])
    firewall.create()
    ctx.instance.runtime_properties[utils.NAME] = firewall.name

@operation
@throw_cloudify_exceptions
def delete_security_group(gcp_config, **kwargs):
    if ctx.instance.runtime_properties.get(utils.TARGET_TAGS):
        ctx.instance.runtime_properties.pop(utils.TARGET_TAGS)
    if ctx.instance.runtime_properties.get(utils.SOURCE_TAGS):
        ctx.instance.runtime_properties.pop(utils.SOURCE_TAGS)
    delete_firewall_rule(gcp_config, **kwargs)


@operation
@throw_cloudify_exceptions
def create_keypair(gcp_config,
                   user,
                   private_key_path,
                   external,
                   private_existing_key_path='',
                   public_existing_key_path='',
                   **kwargs):
    keypair = KeyPair(gcp_config,
                      ctx.logger,
                      user,
                      private_key_path)
    if external:
        keypair.private_key = ctx.get_resource(private_existing_key_path)
        keypair.public_key = ctx.get_resource(public_existing_key_path)
    else:
        keypair.create()
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
    item = get_item_from_gcp_response('name',
                                      instance.name,
                                      instances)
    if relationship:
        ctx.target.instance.runtime_properties['gcp_resource_id'] = \
            item['networkInterfaces'][0]['accessConfigs'][0]['natIP']
    else:
        ctx.instance.runtime_properties['ip'] = \
            item['networkInterfaces'][0]['networkIP']
    # only with one default network interface


def add_to_security_groups(instance):
    provider_config = utils.get_manager_provider_config()
    ctx.logger.info(str(provider_config[utils.AGENTS_SECURITY_GROUP]))
    instance.tags.extend(
        provider_config[utils.AGENTS_SECURITY_GROUP].get(utils.TARGET_TAGS))
