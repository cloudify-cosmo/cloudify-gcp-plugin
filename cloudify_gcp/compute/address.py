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
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import time
from os.path import basename

from cloudify import ctx
from cloudify.decorators import operation

from .. import utils
from cloudify_gcp.gcp import GoogleCloudPlatform
from cloudify_gcp.gcp import check_response


class Address(GoogleCloudPlatform):
    """
    This class handles both Address and GlobalAddress.
    In the API these only differ in that Address requires a
    region, while GlobalAddress does not accept one.
    """

    def __init__(self,
                 config,
                 logger,
                 name,
                 region=None,
                 additional_settings=None,
                 ):
        super(Address, self).__init__(
                config, logger, name,
                additional_settings=additional_settings,
                )
        self.region = region

    def _get_resource_type(self):
        if 'cloudify.gcp.nodes.Address' in ctx.node.type_hierarchy:
            return self.discovery.addresses()
        return self.discovery.globalAddresses()

    def to_dict(self):
        self.body.update({
            'description': 'Cloudify generated Address',
            'name': self.name
        })
        return self.body

    def _common_kwargs(self):
        args = {'project': self.project}
        if 'cloudify.gcp.nodes.Address' in ctx.node.type_hierarchy:
            if self.region:
                args['region'] = self.region
            else:
                args['region'] = self.ZONES[self.config['zone']]['region_name']
        return args

    @check_response
    def get(self):
        return self._get_resource_type().get(
            address=self.name,
            **self._common_kwargs()).execute()

    @utils.async_operation(get=True)
    @check_response
    def create(self):
        return self._get_resource_type().insert(
            body=self.to_dict(),
            **self._common_kwargs()).execute()

    @utils.async_operation()
    @check_response
    def delete(self):
        return self._get_resource_type().delete(
            address=self.name,
            **self._common_kwargs()).execute()


@operation
@utils.throw_cloudify_exceptions
def create(name, additional_settings, region=None, **kwargs):
    name = utils.get_final_resource_name(name)
    gcp_config = utils.get_gcp_config()

    address = Address(
            gcp_config,
            ctx.logger,
            name,
            region=region,
            additional_settings=additional_settings,
            )

    utils.create(address)


@operation
@utils.retry_on_failure('Retrying deleting static IP')
@utils.throw_cloudify_exceptions
def delete(**kwargs):
    gcp_config = utils.get_gcp_config()
    props = ctx.instance.runtime_properties

    if props.get('name'):
        region = props.get('region')
        if region:
            region = basename(region)

        address = Address(
                gcp_config,
                ctx.logger,
                name=props.get('name'),
                region=region,
                )

        utils.delete_if_not_external(address)


def get_reserved_ip_address(static_ip):
    while True:
        response = static_ip.get()
        if response.get('address'):
            return response.get('address')
        time.sleep(2)
