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

from .. import utils
from ..gcp import check_response
from ..gcp import GoogleCloudPlatform


class Network(GoogleCloudPlatform):
    def __init__(self,
                 config,
                 logger,
                 name,
                 auto_subnets=True,
                 additional_settings=None
                 ):
        """
        Create Network object

        :param config: gcp auth file
        :param logger: logger object
        :param network: network dictionary having at least 'name' key

        """
        super(Network, self).__init__(
            config,
            logger,
            utils.get_gcp_resource_name(name),
            additional_settings,
            )
        self.iprange = None
        self.auto_subnets = auto_subnets

    @utils.async_operation(get=True)
    @check_response
    def create(self):
        """
        Create GCP network.
        Global operation.

        :return: REST response with operation responsible for the network
        creation process and its status
        """
        self.logger.info('Create network {0}'.format(self.name))
        return self.discovery.networks().insert(project=self.project,
                                                body=self.to_dict()).execute()

    @utils.async_operation()
    @check_response
    def delete(self):
        """
        Delete GCP network.
        Global operation

        :param network: network name
        :return: REST response with operation responsible for the network
        deletion process and its status
        """
        self.logger.info('Delete network {0}'.format(self.name))
        return self.discovery.networks().delete(
            project=self.project,
            network=self.name).execute()

    @check_response
    def get(self):
        """
        Get GCP network details.

        :return: REST response with operation responsible for the network
        details retrieval
        """
        self.logger.info('Get network {0} details'.format(self.name))
        return self.discovery.networks().get(
            project=self.project,
            network=self.name).execute()

    @check_response
    def list(self):
        """
        List networks.

        :return: REST response with list of networks in a project
        """
        self.logger.info('List networks in project {0}'.format(self.project))
        return self.discovery.networks().list(
            project=self.project).execute()

    def to_dict(self):
        self.body.update({
            'description': 'Cloudify generated network',
            'name': self.name,
            'autoCreateSubnetworks': self.auto_subnets,
        })
        return self.body


@operation
@utils.throw_cloudify_exceptions
def create(name, auto_subnets, additional_settings, **kwargs):
    gcp_config = utils.get_gcp_config()
    name = utils.get_final_resource_name(name)

    network = Network(
            config=gcp_config,
            logger=ctx.logger,
            auto_subnets=auto_subnets,
            name=name,
            additional_settings=additional_settings,
            )

    utils.create(network)


@operation
@utils.throw_cloudify_exceptions
def delete(name=None, **kwargs):
    gcp_config = utils.get_gcp_config()
    props = ctx.instance.runtime_properties

    if props.get('name', None):
        name = props['name']
    else:
        name = utils.get_final_resource_name(name)

    network = Network(
            gcp_config,
            ctx.logger,
            name)

    utils.delete_if_not_external(network)
