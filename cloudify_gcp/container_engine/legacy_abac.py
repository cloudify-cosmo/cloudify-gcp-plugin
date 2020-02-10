# #######
# Copyright (c) 2017-2020 Cloudify Platform Ltd. All rights reserved
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

# Standard library imports
from __future__ import unicode_literals

# Third-party imports
from cloudify import ctx
from cloudify.decorators import operation

# Local imports
from cloudify_gcp import utils
from cloudify_gcp.gcp import check_response
from cloudify_gcp.container_engine import ContainerEngineBase


class LegacyAbac(ContainerEngineBase):
    def __init__(self,
                 config,
                 logger,
                 enabled,
                 cluster_id,
                 name='LegacyAbac',
                 additional_settings=None):
        """
        Create Kubernetes legacy abac cluster object

        :param config:
        :param logger:
        :param name: name of the legacy abac,
         if None project name will be taken
        """
        super(LegacyAbac, self).__init__(config, logger,
                                         name, additional_settings,)
        self.cluster_id = cluster_id
        self.enabled = enabled

    def update_legacy_abac(self):
        return self.discovery_container.clusters().legacyAbac(
            body=self.to_dict(), zone=self.zone,
            projectId=self.project, clusterId=self.cluster_id).execute()

    @check_response
    def create(self):
        return self.update_legacy_abac()

    def to_dict(self):
        return {'enabled': self.enabled}

    @check_response
    def delete(self):
        return self.update_legacy_abac()


@operation(resumable=True)
@utils.throw_cloudify_exceptions
def enable_legacy_abac(enabled, cluster_id, additional_settings, **kwargs):
    gcp_config = utils.get_gcp_config()
    legacy_abac = LegacyAbac(gcp_config,
                             ctx.logger,
                             enabled=enabled,
                             cluster_id=cluster_id,
                             additional_settings=additional_settings)

    utils.set_resource_id_if_use_external(cluster_id)
    utils.create(legacy_abac)


@operation(resumable=True)
@utils.retry_on_failure('Retrying disable legacy abac', delay=15)
@utils.throw_cloudify_exceptions
def disable_legacy_abac(**kwargs):
    gcp_config = utils.get_gcp_config()
    cluster_id = ctx.node.properties.get('cluster_id')
    if cluster_id:
        # Before update legacy abac to the cluster we should check the
        # status of the cluster if it is running or not
        legacy_abac = LegacyAbac(gcp_config, ctx.logger,
                                 enabled=False, cluster_id=cluster_id, )
        utils.delete_if_not_external(legacy_abac)
