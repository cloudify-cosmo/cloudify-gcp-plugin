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
from plugin.gcp import resources

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
def create_instance(config, **kwargs):
    ctx.logger.info('Create instance')
    network = utils.get_gcp_resource_name(config['network'])
    instance = resources.Instance(config['auth'],
                                  config['project'],
                                  ctx.logger,
                                  instance_name=ctx.instance.id,
                                  image=config['agent_image'],
                                  network=network)
    instance.create()
    ctx.instance.runtime_properties[NAME] = instance.name

    set_ip(instance)


@operation
@throw_cloudify_exceptions
def delete_instance(config, **kwargs):
    ctx.logger.info('Delete instance')
    name = ctx.instance.runtime_properties[NAME]
    instance = resources.Instance(config['auth'],
                                  config['project'],
                                  ctx.logger,
                                  instance_name=name)
    instance.delete()
    ctx.instance.runtime_properties.pop(NAME)


@operation
@throw_cloudify_exceptions
def create_network(config, **kwargs):
    ctx.logger.info('Create network')
    network_name = utils.get_gcp_resource_name(config['network'])
    network = resources.Network(config['auth'],
                                config['project'],
                                ctx.logger,
                                network=network_name)
    network.create()
    ctx.instance.runtime_properties[NAME] = network_name


@operation
@throw_cloudify_exceptions
def delete_network(config, **kwargs):
    ctx.logger.info('Delete network')
    network_name = ctx.instance.runtime_properties[NAME]
    network = resources.Network(config['auth'],
                                config['project'],
                                ctx.logger,
                                network=network_name)

    network.delete()
    ctx.instance.runtime_properties.pop(NAME)

@operation
@throw_cloudify_exceptions
def create_firewall_rule(config, **kwargs):
    ctx.logger.info('Create instance')
    network_name = utils.get_gcp_resource_name(config['network'])
    firewall = resources.FirewallRule(config['auth'],
                                      config['project'],
                                      ctx.logger,
                                      firewall=config['firewall'],
                                      network=network_name)

    firewall.create()
    ctx.instance.runtime_properties[NAME] = firewall.name


@operation
@throw_cloudify_exceptions
def delete_firewall_rule(config, **kwargs):
    ctx.logger.info('Create instance')
    network_name = utils.get_gcp_resource_name(config['network'])
    firewall = resources.FirewallRule(config['auth'],
                                      config['project'],
                                      ctx.logger,
                                      firewall=config['firewall'],
                                      network=network_name)
    firewall.delete()
    ctx.instance.runtime_properties.pop(NAME)


def set_ip(instance):
    instances = instance.list()
    item = utils.get_item_from_gcp_response(
        'name',
        ctx.instance.runtime_properties[NAME],
        instances)
    ctx.instance.runtime_properties['ip'] = \
        item['networkInterfaces'][0]['networkIP']
    # only with one default network interface
