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

from gcp import service


@operation
def create_instance(config, **kwargs):
    ctx.logger.info('Create instance')
    compute = service.compute(config['service_account'],
                              config['scope'])
    response = service.create_instance(compute,
                                       config['project'],
                                       config['zone'],
                                       ctx.node.name,
                                       config['agent_image'])
    service.wait_for_operation(compute,
                               config['project'],
                               config['zone'],
                               response['name'])
    service.set_ip(compute, config)


@operation
def delete_instance(config, **kwargs):
    ctx.logger.info('Delete instance')
    compute = service.compute(config['service_account'],
                              config['scope'])
    response = service.delete_instance(compute,
                                       config['project'],
                                       config['zone'],
                                       ctx.node.name)
    service.wait_for_operation(compute,
                               config['project'],
                               config['zone'],
                               response['name'])


@operation
def create_network(config, **kwargs):
    ctx.logger.info('Create network')
    compute = service.compute(config['service_account'],
                              config['scope'])
    response = service.create_network(compute,
                                      config['project'],
                                      config['network'])
    service.wait_for_operation(compute,
                               config['project'],
                               config['zone'],
                               response['name'],
                               True)


@operation
def delete_network(config, **kwargs):
    ctx.logger.info('Delete network')
    compute = service.compute(config['service_account'],
                              config['scope'])
    response = service.delete_network(compute,
                                      config['project'],
                                      config['network'])
    service.wait_for_operation(compute,
                               config['project'],
                               config['zone'],
                               response['name'],
                               True)

@operation
def create_firewall_rule(config, **kwargs):
    ctx.logger.info('Create instance')
    compute = service.compute(config['service_account'],
                              config['scope'])
    response = service.create_firewall_rule(compute,
                                            config['project'],
                                            config['network'],
                                            config['firewall'])
    service.wait_for_operation(compute,
                               config['project'],
                               config['zone'],
                               response['name'],
                               True)


@operation
def delete_firewall_rule(config, **kwargs):
    # config should be taken from node runtime properties
    ctx.logger.info('Create instance')
    compute = service.compute(config['service_account'],
                              config['scope'])
    response = service.delete_firewall_rule(compute,
                                            config['project'],
                                            config['firewall']['name'])
    service.wait_for_operation(compute,
                               config['project'],
                               config['zone'],
                               response['name'],
                               True)
