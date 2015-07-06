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

from gcp.compute import utils
from gcp.compute import constants
from gcp.compute.firewall import FirewallRule
from gcp.compute.instance import Instance
from gcp.compute.network import Network
from gcp.compute.keypair import KeyPair
from gcp.compute.disk import Disk


@operation
@utils.throw_cloudify_exceptions
def create_instance(gcp_config, instance_type, image_id, properties, **kwargs):
    gcp_config['network'] = utils.utils.get_gcp_resource_name(gcp_config['network'])
    script = properties.get('startup_script')
    if script:
        script = ctx.download_resource(script)
    instance = Instance(gcp_config,
                        ctx.logger,
                        name=ctx.instance.id,
                        image=image_id,
                        machine_type=instance_type,
                        external_ip=properties.get('externalIP', False),
                        startup_script=script)
    if ctx.node.properties['install_agent']:
        add_to_security_groups(instance)
    disk = ctx.instance.runtime_properties.get(constants.DISK)
    if disk:
        instance.disks = [disk]
    instance.create()
    ctx.instance.runtime_properties[constants.NAME] = instance.name
    set_ip(instance)


@operation
@utils.throw_cloudify_exceptions
def add_instance_tag(gcp_config, instance_name, tag, **kwargs):
    gcp_config['network'] = utils.get_gcp_resource_name(gcp_config['network'])
    instance = Instance(gcp_config,
                        ctx.logger,
                        name=instance_name)
    instance.set_tags([utils.get_gcp_resource_name(t) for t in tag])


@operation
@utils.throw_cloudify_exceptions
def remove_instance_tag(gcp_config, instance_name, tag, **kwargs):
    if not instance_name:
        return
    gcp_config['network'] = utils.get_gcp_resource_name(gcp_config['network'])
    instance = Instance(gcp_config,
                        ctx.logger,
                        name=instance_name)
    instance.remove_tags([utils.get_gcp_resource_name(t) for t in tag])


@operation
@utils.throw_cloudify_exceptions
def add_external_ip(gcp_config, instance_name, **kwargs):
    # check if the instance has no external ips, only one is supported so far
    gcp_config['network'] = utils.get_gcp_resource_name(gcp_config['network'])
    instance = Instance(gcp_config,
                        ctx.logger,
                        name=instance_name)
    instance.add_access_config()
    set_ip(instance, relationship=True)


@operation
@utils.throw_cloudify_exceptions
def remove_external_ip(gcp_config, instance_name, **kwargs):
    if not instance_name:
        return
    gcp_config['network'] = utils.get_gcp_resource_name(gcp_config['network'])
    instance = Instance(gcp_config,
                        ctx.logger,
                        name=instance_name)
    instance.delete_access_config()


@operation
@utils.throw_cloudify_exceptions
def delete_instance(gcp_config, **kwargs):
    name = ctx.instance.runtime_properties.get(constants.NAME)
    if not name:
        return
    instance = Instance(gcp_config,
                        ctx.logger,
                        name=name)
    instance.delete()
    ctx.instance.runtime_properties.pop(constants.NAME, None)
    ctx.instance.runtime_properties.pop(constants.DISK, None)


@operation
@utils.throw_cloudify_exceptions
def create_network(gcp_config, network, **kwargs):
    network['name'] = utils.get_gcp_resource_name(network['name'])
    network = Network(gcp_config,
                      ctx.logger,
                      network=network)
    network.create()
    ctx.instance.runtime_properties[constants.NAME] = network.name


@operation
@utils.throw_cloudify_exceptions
def delete_network(gcp_config, **kwargs):
    network = {'name': ctx.instance.runtime_properties.get(constants.NAME)}
    if not network['name']:
        return
    network = Network(gcp_config,
                      ctx.logger,
                      network=network)

    network.delete()
    ctx.instance.runtime_properties.pop(constants.NAME, None)


@operation
@utils.throw_cloudify_exceptions
def create_firewall_rule(gcp_config, firewall_rule, **kwargs):
    network_name = utils.get_gcp_resource_name(gcp_config['network'])
    firewall_rule['name'] = utils.get_firewall_rule_name(network_name,
                                                   firewall_rule)
    firewall = FirewallRule(gcp_config,
                            ctx.logger,
                            firewall=firewall_rule,
                            network=network_name)

    firewall.create()
    ctx.instance.runtime_properties[constants.NAME] = firewall.name


@operation
@utils.throw_cloudify_exceptions
def delete_firewall_rule(gcp_config, **kwargs):
    firewall_name = ctx.instance.runtime_properties.get(constants.NAME)
    if not firewall_name:
        return
    network_name = utils.get_gcp_resource_name(gcp_config['network'])
    firewall = {'name': firewall_name}
    firewall = FirewallRule(gcp_config,
                            ctx.logger,
                            firewall=firewall,
                            network=network_name)
    firewall.delete()
    ctx.instance.runtime_properties.pop(constants.NAME, None)


@operation
@utils.throw_cloudify_exceptions
def create_security_group(gcp_config, rules, **kwargs):
    firewall = utils.create_firewall_structure_from_rules(
        gcp_config['network'],
        rules)
    ctx.instance.runtime_properties[constants.TARGET_TAGS] = \
        firewall[constants.TARGET_TAGS]
    ctx.instance.runtime_properties[constants.SOURCE_TAGS] = \
        firewall[constants.SOURCE_TAGS]
    firewall = FirewallRule(gcp_config,
                            ctx.logger,
                            firewall,
                            gcp_config['network'])
    firewall.create()
    ctx.instance.runtime_properties[constants.NAME] = firewall.name


@operation
@utils.throw_cloudify_exceptions
def delete_security_group(gcp_config, **kwargs):
    ctx.instance.runtime_properties.pop(constants.TARGET_TAGS, None)
    ctx.instance.runtime_properties.pop(constants.SOURCE_TAGS, None)
    delete_firewall_rule(gcp_config, **kwargs)


@operation
@utils.throw_cloudify_exceptions
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
    ctx.instance.runtime_properties[constants.PRIVATE_KEY] = keypair.private_key
    ctx.instance.runtime_properties[constants.PUBLIC_KEY] = keypair.public_key
    keypair.save_private_key()


@operation
@utils.throw_cloudify_exceptions
def delete_keypair(gcp_config, user, private_key_path, **kwargs):
    keypair = KeyPair(gcp_config,
                      ctx.logger,
                      user,
                      private_key_path)
    keypair.public_key = ctx.instance.runtime_properties[constants.PUBLIC_KEY]
    keypair.remove_project_ssh_key()
    keypair.remove_private_key()
    ctx.instance.runtime_properties.pop(constants.PRIVATE_KEY, None)
    ctx.instance.runtime_properties.pop(constants.PUBLIC_KEY, None)


@operation
@utils.throw_cloudify_exceptions
def create_disk(gcp_config, image, **kwargs):
    name = utils.get_gcp_resource_name(ctx.instance.id)
    disk = Disk(gcp_config,
                ctx.logger,
                image=image,
                name=name)
    disk.create()
    ctx.instance.runtime_properties[constants.NAME] = name
    ctx.instance.runtime_properties[constants.DISK] = \
        disk.disk_to_insert_instance_dict(name)


@operation
@utils.throw_cloudify_exceptions
def delete_disk(gcp_config, **kwargs):
    name = ctx.instance.runtime_properties[constants.NAME]
    disk = Disk(gcp_config,
                ctx.logger,
                name=name)
    disk.delete()
    ctx.instance.runtime_properties.pop(constants.NAME, None)
    ctx.instance.runtime_properties.pop(constants.DISK, None)


@operation
@utils.throw_cloudify_exceptions
def add_boot_disk(**kwargs):
    disk_body = ctx.target.instance.runtime_properties[constants.DISK]
    disk_body['boot'] = True
    ctx.source.instance.runtime_properties[constants.DISK] = disk_body


@operation
@utils.throw_cloudify_exceptions
def attach_disk(gcp_config, instance_name, disk, **kwargs):
    instance = Instance(gcp_config,
                        ctx.logger,
                        name=instance_name)
    instance.attach_disk(disk)


@operation
@utils.throw_cloudify_exceptions
def detach_disk(gcp_config, instance_name, disk_name, **kwargs):
    instance = Instance(gcp_config,
                        ctx.logger,
                        name=instance_name)
    instance.detach_disk(disk_name)


def set_ip(instance, relationship=False):
    instances = instance.list()
    item = utils.get_item_from_gcp_response('name',
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
    instance.tags.extend(
        provider_config[constants.AGENTS_SECURITY_GROUP]
        .get(constants.TARGET_TAGS))
