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


def init_auth(config, **kwargs):
    flow = None
    if not ctx.instance.runtime_properties.get('credentials'):
        flow = service.init_oauth(config)
        ctx.instance.runtime_properties['credentials'] = True
    return service.authenticate(flow, config['storage'])


@operation
def create_instance(config, **kwargs):
    ctx.logger.info('Create instance')
    credentials = init_auth(config)
    compute = service.compute(credentials)
    response = service.create_instance(compute, config, ctx.node.name)
    service.wait_for_operation(compute, config, response['name'])
    service.set_ip(compute, config)


@operation
def delete_instance(config, **kwargs):
    ctx.logger.info('Delete instance')
    credentials = init_auth(config)
    compute = service.compute(credentials)
    response = service.delete_instance(compute, config, ctx.node.name)
    service.wait_for_operation(compute, config, response['name'])


@operation
def create_network(config, network, **kwargs):
    ctx.logger.info('Create instance')
    credentials = init_auth(config)
    compute = service.compute(credentials)
    response = service.create_network(compute,
                                      config['project'],
                                      network)
    service.wait_for_operation(config, response['name'], compute, True)


@operation
def delete_network(config, network, **kwargs):
    ctx.logger.info('Create instance')
    credentials = init_auth(config)
    compute = service.compute(credentials)
    response = service.delete_network(compute,
                                      config['project'],
                                      network)
    service.wait_for_operation(compute, config, response['name'], True)
