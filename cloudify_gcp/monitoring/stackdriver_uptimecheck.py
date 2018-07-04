# #######
# Copyright (c) 2018 GigaSpaces Technologies Ltd. All rights reserved
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


class StackDriverUpTimeCheckConfig(MonitoringBase):
    def __init__(self, config, logger,
                 project_id=None, uptime_check_config=None, name=None):
        super(StackDriverUpTimeCheckConfig, self).__init__(
            config,
            logger,
            project_id,
            None)
        self.project_id = project_id
        self.uptime_check_config = uptime_check_config
        self.name = name

    @check_response
    def create(self):
        return self.discovery_uptime_check.create(
            parent='projects/{}'.format(self.project_id),
            body=self.uptime_check_config).execute()

    @check_response
    def delete(self):
        return self.discovery_uptime_check.delete(name=self.name).execute()

    @check_response
    def update(self):
        return self.discovery_uptime_check.update(
            name=self.name,
            body=self.uptime_check_config).execute()


@operation
@utils.throw_cloudify_exceptions
def create(project_id, uptime_check_config, **kwargs):
    gcp_config = utils.get_gcp_config()
    group = StackDriverUpTimeCheckConfig(
        gcp_config, ctx.logger,
        project_id=project_id, uptime_check_config=uptime_check_config)
    resource = utils.create(group)
    ctx.instance.runtime_properties['name'] = resource['name']


@operation
@utils.retry_on_failure('Retrying deleting stackdriver group')
@utils.throw_cloudify_exceptions
def delete(**kwargs):
    gcp_config = utils.get_gcp_config()
    group = StackDriverUpTimeCheckConfig(
        gcp_config, ctx.logger, name=ctx.instance.runtime_properties['name'])

    utils.delete_if_not_external(group)


@operation
@utils.throw_cloudify_exceptions
def update(project_id, uptime_check_config, **kwargs):
    gcp_config = utils.get_gcp_config()
    uptime_check = StackDriverUpTimeCheckConfig(
        gcp_config, ctx.logger, project_id, uptime_check_config,
        name=ctx.instance.runtime_properties['name'])
    uptime_check.update()
