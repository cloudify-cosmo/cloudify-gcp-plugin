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

from plugin.gcp.service import GoogleCloudPlatform
from plugin.gcp.service import GCPError
from plugin.gcp import utils


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
    gcp = GoogleCloudPlatform(config['auth'],
                              config['project'],
                              config['scope'],
                              ctx.logger)

    response = gcp.create_instance(ctx.node.name,
                                   network=config['network'],
                                   agent_image=config['agent_image'])
    gcp.wait_for_operation(response['name'])
    set_ip(gcp)


@operation
@throw_cloudify_exceptions
def delete_instance(config, **kwargs):
    gcp = GoogleCloudPlatform(config['auth'],
                              config['project'],
                              config['scope'],
                              ctx.logger)
    response = gcp.delete_instance(ctx.node.name)
    gcp.wait_for_operation(response['name'])


@operation
@throw_cloudify_exceptions
def create_network(config, **kwargs):
    gcp = GoogleCloudPlatform(config['auth'],
                              config['project'],
                              config['scope'],
                              ctx.logger)
    response = gcp.create_network(config['network'])
    gcp.wait_for_operation(response['name'], True)


@operation
@throw_cloudify_exceptions
def delete_network(config, **kwargs):
    gcp = GoogleCloudPlatform(config['auth'],
                              config['project'],
                              config['scope'],
                              ctx.logger)
    response = gcp.delete_network(config['network'])
    gcp.wait_for_operation(response['name'], True)


@operation
@throw_cloudify_exceptions
def create_firewall_rule(config, **kwargs):
    gcp = GoogleCloudPlatform(config['auth'],
                              config['project'],
                              config['scope'],
                              ctx.logger)
    response = gcp.create_firewall_rule(config['network'], config['firewall'])
    gcp.wait_for_operation(response['name'], True)


@operation
@throw_cloudify_exceptions
def delete_firewall_rule(config, **kwargs):
    gcp = GoogleCloudPlatform(config['auth'],
                              config['project'],
                              config['scope'],
                              ctx.logger)
    response = gcp.delete_firewall_rule(config['network'], config['firewall'])
    gcp.wait_for_operation(response['name'], True)


def set_ip(gcp):
    instances = gcp.list_instances()
    item = utils.get_item_from_gcp_response('name', ctx.node.name, instances)
    ctx.instance.runtime_properties['ip'] = \
        item['networkInterfaces'][0]['networkIP']
    # only with one default network interface
