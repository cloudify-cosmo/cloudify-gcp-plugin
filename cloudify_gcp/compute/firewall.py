# #######
# Copyright (c) 2014-2020 Cloudify Platform Ltd. All rights reserved
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

from cloudify import ctx
from cloudify.decorators import operation

from .. import utils
from .. import constants
from cloudify_gcp.gcp import GoogleCloudPlatform
from cloudify_gcp.gcp import check_response


class FirewallRule(GoogleCloudPlatform):
    def __init__(self,
                 config,
                 logger,
                 name,
                 network,
                 allowed=None,
                 sources=None,
                 tags=None,
                 security_group=False,
                 additional_settings=None,
                 ):
        """
        Create Firewall rule object

        :param config:
        :param logger:
        :param firewall: firewall dictionary with a following structure:
        firewall = {constants.NAME: 'firewallname',
                    'allowed: [{ 'IPProtocol': 'tcp', 'ports': ['80']}],
                    'sourceRanges':['0.0.0.0/0'],
                    'sourceTags':['tag'], (optional)
                    'targetTags':['tag2'] (optional)
                    }
        ref. https://cloud.google.com/compute/docs/reference/latest/firewalls
        :param network: network name the firewall rule is connected to
        """
        super(FirewallRule, self).__init__(
            config, logger, ctx.instance.id,
            additional_settings=additional_settings,
            )

        if utils.should_use_external_resource(ctx):
            self.name = utils.assure_resource_id_correct()
        elif name:
            self.name = utils.get_gcp_resource_name(name)
        else:
            self.name = utils.get_gcp_resource_name(ctx.instance.id)

        self.network = network
        self.allowed, self.sources, self.tags = allowed, sources, tags

        self.security_group = security_group

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

        return self.discovery.firewalls().insert(
            project=self.project,
            body=self.to_dict()).execute()

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
            firewall=self.name).execute()

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
            firewall=self.name).execute()

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
            firewall=self.name,
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

    def to_dict(self):
        self.body.update({
            constants.NAME: self.name,
            'description': 'Cloudify generated {}'.format(
                'SG part' if self.security_group else 'FirewallRule'),
            'network': self.network,
            'allowed': [],
            'sourceTags': [],
            'sourceRanges': [],
            })

        for source in self.sources:
            if source[0].isdigit():
                self.body['sourceRanges'].append(source)
            else:
                self.body['sourceTags'].append(source)

        for protocol, ports in self.allowed.items():
            rule = {'IPProtocol': protocol}
            if ports:
                rule['ports'] = ports
                # (no ports is fine and means any port)
            self.body['allowed'].append(rule)

        if self.tags:
            self.body['targetTags'] = self.tags

        return self.body


@operation(resumable=True)
@utils.throw_cloudify_exceptions
def create(name, allowed, sources, target_tags, additional_settings, **kwargs):
    if utils.resource_created(ctx, constants.RESOURCE_ID):
        return

    gcp_config = utils.get_gcp_config()
    network = utils.get_network(ctx)
    name = utils.get_final_resource_name(name)

    firewall = FirewallRule(gcp_config,
                            ctx.logger,
                            network=network,
                            name=name,
                            allowed=allowed,
                            sources=sources,
                            tags=target_tags,
                            additional_settings=additional_settings,
                            )
    ctx.instance.runtime_properties[constants.RESOURCE_ID] = firewall.name
    ctx.instance.runtime_properties[constants.NAME] = firewall.name
    utils.create(firewall)


@operation(resumable=True)
@utils.retry_on_failure('Retrying deleting firewall rule')
@utils.throw_cloudify_exceptions
def delete(**kwargs):
    gcp_config = utils.get_gcp_config()
    firewall_name = ctx.instance.runtime_properties.get(constants.RESOURCE_ID)
    if firewall_name:
        network = utils.get_network(ctx)
        firewall = FirewallRule(gcp_config,
                                ctx.logger,
                                name=firewall_name,
                                network=network)
        utils.delete_if_not_external(firewall)
        # cleanup only if resource is really removed
        if utils.is_object_deleted(firewall):
            ctx.instance.runtime_properties.pop(constants.RESOURCE_ID)
            ctx.instance.runtime_properties.pop(constants.NAME)
