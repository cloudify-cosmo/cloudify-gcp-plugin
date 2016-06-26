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

from gcp.compute import constants
from gcp.compute import utils
from gcp.gcp import GoogleCloudPlatform
from gcp.gcp import check_response


class Network(GoogleCloudPlatform):
    def __init__(self,
                 config,
                 logger,
                 network):
        """
        Create Network object

        :param config: gcp auth file
        :param logger: logger object
        :param network: network dictionary having at least 'name' key

        """
        super(Network, self).__init__(
            config,
            logger,
            utils.get_gcp_resource_name(network['name']))
        self.network = network
        self.iprange = None

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

    def update_model(self):
        self.iprange = self.body['IPv4Range']

    def to_dict(self):
        body = {
            'description': 'Cloudify generated network',
            'name': self.name
        }
        self.body.update(body)
        return self.body


@operation
@utils.throw_cloudify_exceptions
def create(network, **kwargs):
    gcp_config = utils.get_gcp_config()
    network['name'] = utils.get_final_resource_name(network['name'])
    network = Network(gcp_config,
                      ctx.logger,
                      network=network)
    utils.create(network)
    ctx.instance.runtime_properties[constants.NAME] = network.name
    # will be updated only if the resource is created before
    ctx.instance.runtime_properties['ip_range'] = network.iprange


@operation
@utils.retry_on_failure('Retrying deleting network')
@utils.throw_cloudify_exceptions
def delete(**kwargs):
    gcp_config = utils.get_gcp_config()
    name = ctx.instance.runtime_properties.get(constants.NAME, None)
    if not name:
        return
    network = Network(gcp_config,
                      ctx.logger,
                      network={'name': name})
    utils.delete_if_not_external(network)
    ctx.instance.runtime_properties.pop(constants.NAME, None)

    if not utils.is_object_deleted(network):
        ctx.operation.retry('Instance is not yet deleted. Retrying:',
                            constants.RETRY_DEFAULT_DELAY)
