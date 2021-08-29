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
from cloudify_gcp import constants
from cloudify_gcp import utils
from cloudify_gcp.gcp import check_response
from cloudify_gcp.container_engine import ContainerEngineBase


class Cluster(ContainerEngineBase):
    def __init__(self,
                 config,
                 logger,
                 name,
                 additional_settings=None):
        """
        Create Kubernetes cluster object

        :param config:
        :param logger:
        :param name: name of the cluster, if None project name will be taken
        """
        super(Cluster, self).__init__(config,
                                      logger,
                                      name,
                                      additional_settings,)

    @check_response
    def create(self):
        return self.discovery_container.clusters().create(
            body=self.to_dict(), zone=self.zone,
            projectId=self.project).execute()

    def to_dict(self):
        cluster_request = dict()
        cluster_request['cluster'] = dict()

        # The ``name`` field and ``initialNodeCount`` are required fields
        # that must be exists when call create request cluster API
        cluster_request['cluster'].update(
            {constants.NAME: self.name, 'initialNodeCount': 1})

        # Check to see if other request params ``additional_settings`` passed
        # when call create cluster request API to include them
        if self.body:
            cluster_request['cluster'].update(self.body)

        return cluster_request

    @check_response
    def delete(self):
        return self.discovery_container.clusters().delete(
            clusterId=self.name,
            projectId=self.project, zone=self.zone).execute()

    @check_response
    def list(self):
        response = self.discovery_container.clusters().list(
            projectId=self.project, zone=self.zone).execute()
        if 'clusters' in response:
            return response['clusters']
        return []

    @check_response
    def get(self):
        return self.discovery_container.clusters().get(
            clusterId=self.name, projectId=self.project,
            zone=self.zone).execute()


@operation(resumable=True)
@utils.throw_cloudify_exceptions
def create(name, additional_settings, **kwargs):
    if utils.resource_created(ctx, constants.NAME):
        return

    name = utils.get_final_resource_name(name)
    gcp_config = utils.get_gcp_config()
    cluster = Cluster(gcp_config,
                      ctx.logger,
                      name=name,
                      additional_settings=additional_settings)

    utils.create(cluster)
    ctx.instance.runtime_properties.update(cluster.get())
    ctx.instance.runtime_properties[constants.KUBERNETES_CLUSTER] = \
        cluster.get()


@operation(resumable=True)
@utils.throw_cloudify_exceptions
def start(**kwargs):
    gcp_config = utils.get_gcp_config()
    name = ctx.instance.runtime_properties.get(constants.NAME)
    if name:
        cluster = Cluster(gcp_config, ctx.logger, name=name, )
        utils.resource_started(ctx, cluster)


@operation(resumable=True)
@utils.throw_cloudify_exceptions
def delete(**kwargs):
    gcp_config = utils.get_gcp_config()
    name = ctx.instance.runtime_properties.get(constants.NAME)
    if name:
        cluster = Cluster(gcp_config, ctx.logger, name=name, )

        utils.resource_deleted(ctx, cluster)


@operation(resumable=True)
@utils.retry_on_failure('Retrying stopping cluster', delay=15)
@utils.throw_cloudify_exceptions
def stop(**kwargs):
    gcp_config = utils.get_gcp_config()
    name = ctx.instance.runtime_properties.get(constants.NAME)
    if name:
        cluster = Cluster(gcp_config,
                          ctx.logger,
                          name=name,)
        utils.delete_if_not_external(cluster)
