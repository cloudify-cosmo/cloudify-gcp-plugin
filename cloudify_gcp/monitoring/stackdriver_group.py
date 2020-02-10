# #######
# Copyright (c) 2018-2020 Cloudify Platform Ltd. All rights reserved
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

from cloudify_gcp.gcp import check_response
from .. import utils
from ..monitoring import MonitoringBase


class StackDriverGroup(MonitoringBase):
    def __init__(self,
                 config,
                 logger,
                 project_id=None,
                 display_name=None,
                 parent_name=None,
                 filter_name=None,
                 name=None,
                 is_cluster=False,
                 group_id=None,
                 additional_settings=None,
                 **kwargs):
        super(StackDriverGroup, self).__init__(
            config, logger, display_name, additional_settings)
        self.display_name = display_name
        self.group_id = group_id
        self.project_id = project_id
        self.parent_name = parent_name
        self.filter_name = filter_name
        self.is_cluster = is_cluster
        self.name = name or 'projects/{}/groups/{}'.format(
            self.project_id, self.group_id)

    def to_dict(self):
        body = {
            'displayName': self.display_name,
            'parentName': self.parent_name,
            'filter': self.filter_name,
            'isCluster': self.is_cluster
        }
        return body

    @check_response
    def create(self):
        return self.discovery_groups.create(
            name='projects/{}'.format(self.project_id),
            body=self.to_dict()).execute()

    @check_response
    def get(self):
        return self.discovery_groups.get(name=self.name).execute()

    @check_response
    def delete(self):
        return self.discovery_groups.delete(name=self.name).execute()

    @check_response
    def update(self):
        return self.discovery_groups.update(
            name=self.name, body=self.to_dict()).execute()


@operation
@utils.throw_cloudify_exceptions
def create(project_id, display_name, parent_name, filter_name, **kwargs):
    gcp_config = utils.get_gcp_config()
    group = StackDriverGroup(gcp_config, ctx.logger, project_id,
                             display_name, parent_name, filter_name, **kwargs)
    resource = utils.create(group)
    ctx.instance.runtime_properties['name'] = resource['name']


@operation
@utils.retry_on_failure('Retrying deleting stackdriver group')
@utils.throw_cloudify_exceptions
def delete(**kwargs):
    gcp_config = utils.get_gcp_config()
    group = StackDriverGroup(gcp_config, ctx.logger,
                             name=ctx.instance.runtime_properties['name'])

    utils.delete_if_not_external(group)


@operation
@utils.throw_cloudify_exceptions
def update(project_id, display_name, parent_name, filter_name, **kwargs):
    gcp_config = utils.get_gcp_config()
    current_resource_name = ctx.instance.runtime_properties['name']
    group = StackDriverGroup(gcp_config, ctx.logger, project_id,
                             display_name, parent_name, filter_name,
                             name=current_resource_name, **kwargs)
    group.update()
