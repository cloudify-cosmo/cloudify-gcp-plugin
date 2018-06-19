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


class MonitoringService(ContainerEngineBase):
    def __init__(self,
                 config,
                 logger,
                 service_type,
                 cluster_id,
                 name='MonitoringService',
                 additional_settings=None):
        """
        Create Kubernetes monitoring service cluster object

        :param config:
        :param logger:
        :param name: name of the monitoring service,
         if None project name will be taken
        """
        super(MonitoringService, self).__init__(config, logger,
                                                name, additional_settings,)
        self.cluster_id = cluster_id
        self.service_type = service_type

    def update_monitoring_service(self):
        return self.discovery_container.clusters().monitoring(
            body=self.to_dict(), zone=self.zone,
            projectId=self.project, clusterId=self.cluster_id).execute()

    @check_response
    def create(self):
        return self.update_monitoring_service()

    def to_dict(self):
        return {'monitoringService': self.service_type}

    @check_response
    def delete(self):
        self.service_type = 'none'
        return self.update_monitoring_service()


@operation
@utils.retry_on_failure('Retrying set monitoring service', delay=15)
@utils.throw_cloudify_exceptions
def set_monitoring_service(monitoring_service, cluster_id,
                           additional_settings, **kwargs):
    name = utils.get_final_resource_name(monitoring_service)
    gcp_config = utils.get_gcp_config()
    service = MonitoringService(gcp_config,
                                ctx.logger,
                                service_type=name,
                                cluster_id=cluster_id,
                                additional_settings=additional_settings)

    utils.set_resource_id_if_use_external(name)
    utils.create(service)


@operation
@utils.retry_on_failure('Retrying unset monitoring service', delay=15)
@utils.throw_cloudify_exceptions
def unset_monitoring_service(**kwargs):
    gcp_config = utils.get_gcp_config()
    cluster_id = ctx.node.properties.get('cluster_id')
    if cluster_id:
        # Before update monitoring service to the cluster we should check the
        # status of the cluster if it is running or not
        service = MonitoringService(gcp_config, ctx.logger,
                                    service_type='none',
                                    cluster_id=cluster_id, )

        utils.delete_if_not_external(service)
