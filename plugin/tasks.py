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

from plugin.gcp.service import GoogleCloudPlatform


@operation
def create_instance(config, **kwargs):
    ctx.logger.info('Create instance')
    gcp = GoogleCloudPlatform(config['auth'],
                              config['project'],
                              config['scope'])
    response = gcp.create_instance(ctx.node.name,
                                   config['agent_image'])
    gcp.wait_for_operation(response['name'])
    gcp.set_ip()


@operation
def delete_instance(config, **kwargs):
    ctx.logger.info('Delete instance')
    gcp = GoogleCloudPlatform(config['auth'],
                              config['project'],
                              config['scope'])
    response = gcp.delete_instance(ctx.node.name)
    gcp.wait_for_operation(response['name'])


@operation
def create_network(config, **kwargs):
    ctx.logger.info('Create network')
    gcp = GoogleCloudPlatform(config['auth'],
                              config['project'],
                              config['scope'])
    response = gcp.create_network(config['network'])
    gcp.wait_for_operation(response['name'], True)


@operation
def delete_network(config, **kwargs):
    ctx.logger.info('Delete network')
    gcp = GoogleCloudPlatform(config['auth'],
                              config['project'],
                              config['scope'])
    response = gcp.delete_network(config['network'])
    gcp.wait_for_operation(response['name'], True)


@operation
def create_firewall_rule(config, **kwargs):
    ctx.logger.info('Create instance')
    gcp = GoogleCloudPlatform(config['auth'],
                              config['project'],
                              config['scope'])
    response = gcp.create_firewall_rule(config['network'], config['firewall'])
    gcp.wait_for_operation(response['name'], True)


@operation
def delete_firewall_rule(config, **kwargs):
    ctx.logger.info('Create instance')
    gcp = GoogleCloudPlatform(config['auth'],
                              config['project'],
                              config['scope'])
    response = gcp.delete_firewall_rule(config['network'], config['firewall'])
    gcp.wait_for_operation(response['name'], True)
