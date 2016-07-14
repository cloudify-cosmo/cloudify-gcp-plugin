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
import time

from cloudify import ctx
from cloudify.decorators import operation

from gcp.compute import utils
from gcp.compute import constants
from gcp.gcp import GoogleCloudPlatform
from gcp.gcp import check_response


class StaticIP(GoogleCloudPlatform):
    def __init__(self,
                 config,
                 logger,
                 name,
                 ip=None,
                 additional_settings=None):
        super(StaticIP, self).__init__(config,
                                       logger,
                                       name,
                                       additional_settings)

    def to_dict(self):
        self.body.update({
            'description': 'Cloudify generated Static IP',
            'name': self.name
        })
        return self.body

    @check_response
    def get(self):
        return self.discovery.globalAddresses().get(
            project=self.project,
            address=self.name).execute()

    @check_response
    def create(self):
        return self.discovery.globalAddresses().insert(
            project=self.project,
            body=self.to_dict()).execute()

    @check_response
    def delete(self):
        return self.discovery.globalAddresses().delete(
            project=self.project,
            address=self.name).execute()


@operation
@utils.throw_cloudify_exceptions
def create(name, additional_settings, **kwargs):
    name = utils.get_final_resource_name(name)
    gcp_config = utils.get_gcp_config()
    static_ip = StaticIP(gcp_config,
                         ctx.logger,
                         name,
                         additional_settings)
    utils.create(static_ip)
    ip_address = get_reserved_ip_address(static_ip)
    ctx.instance.runtime_properties[constants.NAME] = name
    ctx.instance.runtime_properties[constants.IP] = ip_address


@operation
@utils.retry_on_failure('Retrying deleting static IP')
@utils.throw_cloudify_exceptions
def delete(**kwargs):
    gcp_config = utils.get_gcp_config()
    name = ctx.instance.runtime_properties.get(constants.NAME, None)
    if name:
        static_ip = StaticIP(gcp_config,
                             ctx.logger,
                             name=name)
        utils.delete_if_not_external(static_ip)
        ctx.instance.runtime_properties.pop(constants.NAME, None)
        ctx.instance.runtime_properties.pop(constants.IP, None)


def get_reserved_ip_address(static_ip):
    while True:
        response = static_ip.get()
        if response.get('address'):
            return response.get('address')
        time.sleep(2)
