# #######
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
from gcp.gcp import GoogleCloudPlatform
from gcp.gcp import check_response


class GlobalForwardingRule(GoogleCloudPlatform):
    def __init__(self,
                 config,
                 logger,
                 name,
                 target_proxy=None,
                 port_range=None,
                 ip_address=None):
        super(GlobalForwardingRule, self).__init__(config, logger, name)
        self.target_proxy = target_proxy
        self.port_range = port_range
        self.ip_address = ip_address

    def to_dict(self):
        body = {
            'description': 'Cloudify generated Global Forwarding Rule',
            'name': self.name,
            'target': self.target_proxy,
            'portRange': self.port_range,
            'IPAddress': self.ip_address
        }
        return body

    @check_response
    def get(self):
        return self.discovery.globalForwardingRules().get(
            project=self.project,
            forwardingRule=self.name).execute()

    @check_response
    def list(self):
        return self.discovery.globalForwardingRules().list(
            project=self.project).execute()

    @check_response
    def create(self):
        return self.discovery.globalForwardingRules().insert(
            project=self.project,
            body=self.to_dict()).execute()

    @check_response
    def delete(self):
        return self.discovery.globalForwardingRules().delete(
            project=self.project,
            forwardingRule=self.name).execute()


@operation
@utils.throw_cloudify_exceptions
def create(name, target_proxy, port_range, ip_address, **kwargs):
    name = utils.get_final_resource_name(name)
    gcp_config = utils.get_gcp_config()
    forwarding_rule = GlobalForwardingRule(gcp_config,
                                           ctx.logger,
                                           name,
                                           target_proxy,
                                           port_range,
                                           ip_address)
    utils.create(forwarding_rule)
    ctx.instance.runtime_properties[constants.NAME] = name


@operation
@utils.retry_on_failure('Retrying deleting global forwarding rule')
@utils.throw_cloudify_exceptions
def delete(**kwargs):
    gcp_config = utils.get_gcp_config()
    name = ctx.instance.runtime_properties.get(constants.NAME, None)
    if name:
        forwarding_rule = GlobalForwardingRule(gcp_config,
                                               ctx.logger,
                                               name=name)
        utils.delete_if_not_external(forwarding_rule)
        ctx.instance.runtime_properties.pop(constants.NAME, None)
