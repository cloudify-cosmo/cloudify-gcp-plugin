# #######
# Copyright (c) 2017 GigaSpaces Technologies Ltd. All rights reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Standard library imports
from __future__ import unicode_literals

# Third-party imports
from cloudify import ctx
from cloudify.decorators import operation

# Local imports
from cloudify_gcp import utils
from cloudify_gcp.gcp import check_response
from cloudify_gcp.container_engine import ContainerEngineBase


class NetworkPolicy(ContainerEngineBase):
    def __init__(self,
                 config,
                 logger,
                 network_policy_config,
                 cluster_id,
                 name='NetworkPolicy',
                 additional_settings=None):
        """
        Create Kubernetes network policy cluster object

        :param config:
        :param logger:
        :param name: name of the legacy abac,
         if None project name will be taken
        """
        super(NetworkPolicy, self).__init__(config, logger,
                                            name, additional_settings,)
        self.cluster_id = cluster_id
        self.network_policy_config = network_policy_config

    def update_network_policy(self, body):
        return self.discovery_container.clusters().setNetworkPolicy(
            body=body, zone=self.zone,
            projectId=self.project, clusterId=self.cluster_id).execute()

    @check_response
    def create(self):
        return self.update_network_policy(self.to_dict())

    @check_response
    def delete(self):
        return self.update_network_policy(self.to_dict())

    @check_response
    def update_network_policy_addon(self, body):
        return self.discovery_container.clusters().update(
            body=body, zone=self.zone,
            projectId=self.project, clusterId=self.cluster_id).execute()

    def to_dict(self):
        return {'networkPolicy': self.network_policy_config}


def update_network_policy_addon(cluster_id, enabled):
    gcp_config = utils.get_gcp_config()
    network_policy = NetworkPolicy(gcp_config, ctx.logger, None,
                                   cluster_id=cluster_id,
                                   additional_settings={})

    policy_addon_object = dict()
    policy_addon_object['update'] = \
        {
            'desiredAddonsConfig': {
                'networkPolicyConfig': {
                    'disabled': not enabled
                }
            }
        }
    network_policy.update_network_policy_addon(policy_addon_object)


@operation
@utils.retry_on_failure('Retrying enable network policy addon', delay=15)
@utils.throw_cloudify_exceptions
def enable_network_policy_addon(cluster_id, **kwargs):

    update_network_policy_addon(cluster_id, True)
    ctx.instance.runtime_properties['cluster_id'] = cluster_id

    utils.set_resource_id_if_use_external(cluster_id)


@operation
@utils.retry_on_failure('Retrying disable network policy addon', delay=15)
@utils.throw_cloudify_exceptions
def disable_network_policy_addon(**kwargs):
    cluster_id = ctx.instance.runtime_properties['cluster_id']
    update_network_policy_addon(cluster_id, False)


@operation
@utils.retry_on_failure(
    'Retrying creating network policy configuration', delay=15)
@utils.throw_cloudify_exceptions
def create_network_policy_config(network_policy_config,
                                 additional_settings, **kwargs):
    gcp_config = utils.get_gcp_config()

    cluster_id = ctx.instance.runtime_properties['cluster_id']

    network_policy = NetworkPolicy(gcp_config, ctx.logger,
                                   network_policy_config=network_policy_config,
                                   cluster_id=cluster_id,
                                   additional_settings=additional_settings)
    utils.create(network_policy)


@operation
@utils.retry_on_failure(
    'Retrying deleting network policy configuration', delay=15)
@utils.throw_cloudify_exceptions
def delete_network_policy_config(**kwargs):
    gcp_config = utils.get_gcp_config()
    cluster_id = ctx.instance.runtime_properties['cluster_id']
    network_policy_config = {'enabled': False,
                             'provider': 'PROVIDER_UNSPECIFIED'
                             }
    if cluster_id:
        network_policy = \
            NetworkPolicy(gcp_config, ctx.logger,
                          network_policy_config=network_policy_config,
                          cluster_id=cluster_id,)
        utils.delete_if_not_external(network_policy)
