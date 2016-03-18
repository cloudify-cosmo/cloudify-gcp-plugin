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
        super(FirewallRule, self).__init__(config, logger, firewall['name'])
        self.firewall = firewall
        self.network = network

    @check_response
    def create(self):
        """
        Create GCP firewall rule in a GCP network.
        Global operation.

        :return: REST response with operation responsible for the firewall rule
        creation process and its status
        """
        self.logger.info(
            'Create firewall rule {0} in network {1}'.format(
                self.name,
                self.network))

        self.firewall['network'] = 'global/networks/{0}'.format(self.network)
        return self.discovery.firewalls().insert(
            project=self.project,
            body=self.firewall).execute()

    @check_response
    def delete(self):
        """
        Delete GCP firewall rule from GCP network.
        Global operation.

        :return: REST response with operation responsible for the firewall rule
        deletion process and its status
        """
        self.logger.info(
            'Delete firewall rule {0} from network {1}'.format(
                self.name,
                self.network))

        return self.discovery.firewalls().delete(
            project=self.project,
            firewall=self.firewall['name']).execute()

    @check_response
    def get(self):
        """
        Get GCP firewall rule details.

        :return: REST response with operation responsible for the firewall
        rule details retrieval
        """
        self.logger.info('Get firewall rule {0} details'.format(self.name))

        return self.discovery.firewalls().get(
            project=self.project,
            firewall=self.firewall['name']).execute()

    @check_response
    def update(self):
        """
        Update GCP firewall rule.
        Global operation.

        :return: REST response with operation responsible for the firewall rule
        update process and its status
        """
        self.logger.info('Update firewall rule {0}'.format(self.name))

        return self.discovery.firewalls().update(
            project=self.project,
            firewall=self.firewall['name'],
            body=self.firewall).execute()

    @check_response
    def list(self):
        """
        List GCP firewall rules in all networks.

        :return: REST response with list of firewall rules in a project
        """
        self.logger.info(
            'List firewall rules in project {0}'.format(self.project))

        return self.discovery.firewalls().list(
            project=self.project).execute()


@operation
@utils.throw_cloudify_exceptions
def create(firewall_rule, name, **kwargs):
    gcp_config = utils.get_gcp_config()
    network_name = utils.get_gcp_resource_name(gcp_config['network'])
    set_firewall_rule_name(firewall_rule, network_name, name)
    firewall = FirewallRule(gcp_config,
                            ctx.logger,
                            firewall=firewall_rule,
                            network=network_name)

    utils.create(firewall)
    ctx.instance.runtime_properties[constants.NAME] = firewall.name


def set_firewall_rule_name(firewall_rule, network_name, name):
    if utils.should_use_external_resource():
        firewall_rule['name'] = utils.assure_resource_id_correct()
    elif name:
        firewall_rule['name'] = utils.get_gcp_resource_name(name)
    else:
        firewall_rule['name'] = utils.get_firewall_rule_name(network_name,
                                                             firewall_rule)


@operation
@utils.retry_on_failure('Retrying deleting firewall rule')
@utils.throw_cloudify_exceptions
def delete(**kwargs):
    gcp_config = utils.get_gcp_config()
    firewall_name = ctx.instance.runtime_properties.get(constants.NAME, None)
    if not firewall_name:
        return
    network_name = utils.get_gcp_resource_name(gcp_config['network'])
    firewall = FirewallRule(gcp_config,
                            ctx.logger,
                            firewall={'name': firewall_name},
                            network=network_name)
    utils.delete_if_not_external(firewall)
    ctx.instance.runtime_properties.pop(constants.NAME, None)


@operation
@utils.throw_cloudify_exceptions
def create_security_group(rules, name, **kwargs):
    gcp_config = utils.get_gcp_config()
    firewall_structure = create_firewall_structure_from_rules(
        gcp_config['network'],
        rules,
        name)
    ctx.instance.runtime_properties[constants.TARGET_TAGS] = \
        firewall_structure[constants.TARGET_TAGS]
    ctx.instance.runtime_properties[constants.SOURCE_TAGS] = \
        firewall_structure[constants.SOURCE_TAGS]
    firewall = FirewallRule(gcp_config,
                            ctx.logger,
                            firewall_structure,
                            gcp_config['network'])
    ctx.instance.runtime_properties[constants.NAME] = firewall.name
    utils.create(firewall)


def create_firewall_structure_from_rules(network, rules, name):
    firewall_structure = utils.create_firewall_structure_from_rules(
        network,
        rules)
    if utils.should_use_external_resource():
        firewall_structure['name'] = utils.assure_resource_id_correct()
    elif name:
        firewall_structure['name'] = utils.get_gcp_resource_name(name)
    return firewall_structure


@operation
@utils.throw_cloudify_exceptions
def delete_security_group(**kwargs):
    ctx.instance.runtime_properties.pop(constants.TARGET_TAGS, None)
    ctx.instance.runtime_properties.pop(constants.SOURCE_TAGS, None)
    delete(**kwargs)
