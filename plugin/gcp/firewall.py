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
from plugin.gcp.service import GoogleCloudPlatform
from plugin.gcp.service import blocking


class FirewallRule(GoogleCloudPlatform):
    def __init__(self,
                 config,
                 logger,
                 firewall,
                 network):
        """
        Create Firewall rule object

        :param config:
        :param logger:
        :param firewall: firewall dictionary with a following structure:
        firewall = {'name': 'firewallname',
                    'allowed: [{ 'IPProtocol': 'tcp', 'ports': ['80']}],
                    'sourceRanges':['0.0.0.0/0'],
                    'sourceTags':['tag'], (optional)
                    'targetTags':['tag2'] (optional)
                    }
        ref. https://cloud.google.com/compute/docs/reference/latest/firewalls
        :param network: network name the firewall rule is connected to
        """
        super(FirewallRule, self).__init__(config, logger)
        self.firewall = firewall
        self.network = network
        self.name = self.firewall['name']

    @blocking
    def create(self):
        """
        Create GCP firewall rule in a GCP network.
        Global operation.

        :return: REST response with operation responsible for the firewall rule
        creation process and its status
        """
        self.logger.info('Create firewall rule')
        self.firewall['network'] = 'global/networks/{0}'.format(self.network)
        return self.compute.firewalls().insert(
            project=self.project,
            body=self.firewall).execute()

    @blocking
    def delete(self):
        """
        Delete GCP firewall rule from GCP network.
        Global operation.

        :return: REST response with operation responsible for the firewall rule
        deletion process and its status
        """
        self.logger.info('Delete firewall rule')
        return self.compute.firewalls().delete(
            project=self.project,
            firewall=self.firewall['name']).execute()

    @blocking
    def update(self):
        """
        Update GCP firewall rule.
        Global operation.

        :return: REST response with operation responsible for the firewall rule
        update process and its status
        """
        self.logger.info('Update firewall rule')
        return self.compute.firewalls().update(
            project=self.project,
            firewall=self.firewall['name'],
            body=self.firewall).execute()

    def list(self):
        """
        List GCP firewall rules in all networks.

        :return: REST response with list of firewall rules in a project
        """
        self.logger.info('List firewall rules in project')
        return self.compute.firewalls().list(
            project=self.project).execute()

    def wait_for_operation(self, operation, global_operation=True):
        super(FirewallRule, self).wait_for_operation(operation,
                                                     global_operation)
