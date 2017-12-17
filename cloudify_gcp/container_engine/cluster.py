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
#    * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    * See the License for the specific language governing permissions and
#    * limitations under the License.

# Standard library imports
from __future__ import unicode_literals
from six.moves import http_client

# Third-party imports
from cloudify import ctx
from cloudify.decorators import operation
from cloudify.exceptions import NonRecoverableError
from googleapiclient.errors import HttpError

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
            {'name': self.name, 'initialNodeCount': 1})

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
        return response['clusters']

    @check_response
    def get(self):
        return self.discovery_container.clusters().get(
            clusterId=self.name, projectId=self.project,
            zone=self.zone).execute()


@operation
@utils.throw_cloudify_exceptions
def create(name, additional_settings, **kwargs):
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


@operation
@utils.throw_cloudify_exceptions
def start(**kwargs):
    gcp_config = utils.get_gcp_config()
    name = ctx.instance.runtime_properties.get('name')
    if name:
        cluster = Cluster(gcp_config, ctx.logger, name=name, )
        cluster_status = cluster.get()['status'] if cluster.get() else None
        if cluster_status == constants.KUBERNETES_RUNNING_STATUS:
            ctx.logger.debug('Kubernetes cluster running.')

        elif cluster_status == constants.KUBERNETES_PROVISIONING_STATUS:
            ctx.operation.retry(
                'Kubernetes cluster is still provisioning.', 15)

        elif cluster_status == constants.KUBERNETES_ERROR_STATUS:
            raise NonRecoverableError('Kubernetes cluster in error state.')

        else:
            ctx.logger.warn(
                'cluster status is neither {0}, {1}, {2}.'
                ' Unknown Status: {3}'.format(
                    constants.KUBERNETES_RUNNING_STATUS,
                    constants.KUBERNETES_PROVISIONING_STATUS,
                    constants.KUBERNETES_ERROR_STATUS, cluster_status))


@operation
@utils.throw_cloudify_exceptions
def delete(**kwargs):
    gcp_config = utils.get_gcp_config()
    name = ctx.instance.runtime_properties.get('name')
    if name:
        cluster = Cluster(gcp_config, ctx.logger, name=name, )
        try:
            cluster_status = cluster.get()['status'] if cluster.get() else None
            if cluster_status == constants.KUBERNETES_STOPPING_STATUS:
                ctx.operation.retry(
                    'Kubernetes cluster is still de-provisioning', 15)

            elif cluster_status == constants.KUBERNETES_ERROR_STATUS:
                raise NonRecoverableError(
                    'Kubernetes cluster failed to delete.')

        except HttpError as e:
            if e.resp.status == http_client.NOT_FOUND:
                ctx.logger.debug('Kubernetes cluster deleted.')
            else:
                raise e


@operation
@utils.retry_on_failure('Retrying stopping cluster', delay=15)
@utils.throw_cloudify_exceptions
def stop(**kwargs):
    gcp_config = utils.get_gcp_config()
    name = ctx.instance.runtime_properties.get('name')
    if name:
        cluster = Cluster(gcp_config,
                          ctx.logger,
                          name=name,)
        utils.delete_if_not_external(cluster)
