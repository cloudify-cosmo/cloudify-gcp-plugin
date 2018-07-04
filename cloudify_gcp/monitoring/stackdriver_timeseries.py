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


class StackDriverTimeSeries(MonitoringBase):
    def __init__(self, config, logger, project_id, time_series):
        super(StackDriverTimeSeries, self).__init__(
            config,
            logger,
            project_id,
            None)
        self.project_id = project_id
        self.time_series = time_series

    @check_response
    def create(self):
        return self.discovery_time_series.create(
            name='projects/{}'.format(self.project_id),
            body=self.time_series).execute()


@operation
@utils.throw_cloudify_exceptions
def create(project_id, time_series, **kwargs):
    gcp_config = utils.get_gcp_config()
    group = StackDriverTimeSeries(
        gcp_config, ctx.logger, project_id, time_series)
    resource = utils.create(group)

    if resource:
        ctx.logger.warn(
            'Some time series could not be written {}'.format(resource))
