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
from six.moves import http_client

# Third-party imports
from cloudify import ctx
from cloudify.decorators import operation
from googleapiclient.errors import HttpError

# Local imports
from cloudify_gcp import constants
from cloudify_gcp import utils
from cloudify_gcp.gcp import check_response
from cloudify_gcp.container_engine import ContainerEngineBase


class NodePool(ContainerEngineBase):
    def __init__(self,
                 config,
                 logger,
                 name,
                 cluster_id,
                 additional_settings=None):
        """
        Create Kubernetes node pool object

        :param config:
        :param logger:
        :param name: name of the node pool, if None project name will be taken
        """
        super(NodePool, self).__init__(config,
                                       logger,
                                       name,
                                       additional_settings,)
        self.cluster_id = cluster_id

    @check_response
    def create(self):
        return self.discovery_container.nodePools().create(
            body=self.to_dict(), zone=self.zone,
            projectId=self.project, clusterId=self.cluster_id).execute()

    def to_dict(self):
        node_pool_request = dict()
        node_pool_request['nodePool'] = dict()

        # The ``name`` field and ``initialNodeCount`` are required fields
        # that must be exists when call create request node pool API
        node_pool_request['nodePool'].update(
            {constants.NAME: self.name})

        # Check to see if other request params ``additional_settings`` passed
        # when call create node pool request API to include them
        if self.body:
            node_pool_request['nodePool'].update(self.body)

        return node_pool_request

    @check_response
    def delete(self):
        return self.discovery_container.nodePools().delete(
            nodePoolId=self.name, zone=self.zone,
            projectId=self.project, clusterId=self.cluster_id).execute()

    @check_response
    def list(self):
        response = self.discovery_container.nodePools().list(
            projectId=self.project, zone=self.zone,
            clusterId=self.cluster_id).execute()
        return response['nodePools']

    @check_response
    def get(self):
        return self.discovery_container.nodePools().get(
            nodePoolId=self.name, clusterId=self.cluster_id,
            projectId=self.project, zone=self.zone).execute()

    @property
    def discovery_container(self):
        return self.discovery.projects().zones().clusters() if self.discovery \
            else None


def get_node(node_pool):
    try:
        created_node = node_pool.get()
    except HttpError as e:
        if e.resp.status == http_client.NOT_FOUND:
            return None
        else:
            raise e

    return created_node


@operation(resumable=True)
@utils.retry_on_failure('Retrying adding node pool', delay=15)
@utils.throw_cloudify_exceptions
def create(name, cluster_id, additional_settings, **kwargs):
    if utils.resorce_created(ctx, constants.NAME):
        return

    name = utils.get_final_resource_name(name)
    gcp_config = utils.get_gcp_config()
    node_pool = NodePool(gcp_config,
                         ctx.logger,
                         name=name,
                         cluster_id=cluster_id,
                         additional_settings=additional_settings)

    utils.create(node_pool)
    ctx.instance.runtime_properties[constants.NAME] = name
    ctx.instance.runtime_properties['cluster_id'] = cluster_id


@operation(resumable=True)
@utils.throw_cloudify_exceptions
def start(**kwargs):
    name = ctx.instance.runtime_properties[constants.NAME]
    cluster_id = ctx.instance.runtime_properties['cluster_id']
    gcp_config = utils.get_gcp_config()
    node_pool = NodePool(gcp_config, ctx.logger, name=name,
                         cluster_id=cluster_id, additional_settings={})

    created_node = get_node(node_pool)
    if not created_node:
        ctx.operation.retry(
            'Kubernetes node pool {0} '
            'is still provisioning'.format(name), 15)

    ctx.logger.debug('Node pool {0} started successfully'.format(name))
    ctx.instance.runtime_properties[
        constants.KUBERNETES_NODE_POOL] = created_node


@operation(resumable=True)
@utils.retry_on_failure('Retrying removing node pool', delay=15)
@utils.throw_cloudify_exceptions
def stop(**kwargs):
    gcp_config = utils.get_gcp_config()
    name = ctx.instance.runtime_properties.get(constants.NAME)
    cluster_id = ctx.instance.runtime_properties.get('cluster_id')
    if name:

        node_pool = NodePool(gcp_config, ctx.logger,
                             name=name, cluster_id=cluster_id,)

        remote_mode = get_node(node_pool)
        if remote_mode:
            utils.delete_if_not_external(node_pool)
        else:
            ctx.operation.retry(
                'Node pool {0} stopped'.format(name))


@operation(resumable=True)
@utils.throw_cloudify_exceptions
def delete(**kwargs):
    gcp_config = utils.get_gcp_config()
    name = ctx.instance.runtime_properties.get(constants.NAME)
    cluster_id = ctx.node.properties.get('cluster_id')
    if name:

        node_pool = NodePool(gcp_config, ctx.logger,
                             name=name, cluster_id=cluster_id,)

        remote_mode = get_node(node_pool)
        if not remote_mode:
            ctx.operation.retry(
                'Node pool {0} deleted successfully'.format(name))
