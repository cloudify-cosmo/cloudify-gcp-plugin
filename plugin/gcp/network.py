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
from plugin.gcp import utils
from plugin.gcp.service import GoogleCloudPlatform
from plugin.gcp.service import blocking


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
        super(Network, self).__init__(config, logger)
        self.network = network
        self.name = utils.get_gcp_resource_name(network['name'])

    @blocking
    def create(self):
        """
        Create GCP network.
        Global operation.

        :return: REST response with operation responsible for the network
        creation process and its status
        """
        self.logger.info('Create network {0}'.format(self.name))
        return self.compute.networks().insert(project=self.project,
                                              body=self.to_dict()).execute()

    @blocking
    def delete(self):
        """
        Delete GCP network.
        Global operation

        :param network: network name
        :return: REST response with operation responsible for the network
        deletion process and its status
        """
        self.logger.info('Delete network {0}'.format(self.name))
        return self.compute.networks().delete(
            project=self.project,
            network=self.name).execute()

    def list(self):
        """
        List networks.

        :return: REST response with list of networks in a project
        """
        self.logger.info('List networks in project {0}'.format(self.project))
        return self.compute.networks().list(
            project=self.project).execute()

    def wait_for_operation(self, operation, global_operation=True):
        super(Network, self).wait_for_operation(operation, global_operation)

    def to_dict(self):
        body = {
            'description': 'Cloudify generated network',
            'name': self.name
        }
        return body
