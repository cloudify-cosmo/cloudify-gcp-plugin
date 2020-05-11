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
from .. import _compat
from cloudify_gcp.gcp import GoogleCloudPlatform
from .. import constants


class MonitoringBase(GoogleCloudPlatform, _compat.ABC):

    def __init__(self, config, logger, name,
                 additional_settings=None,
                 scope=(constants.CONTAINER_SCOPE, constants.MONITORING_SCOPE),
                 discovery=constants.MONITORING_DISCOVERY,
                 api_version=constants.API_V3):
        super(MonitoringBase, self).__init__(
            config, logger, name,
            additional_settings, scope, discovery, api_version)

    @property
    def discovery_groups(self):
        return self.discovery.projects().groups()

    @property
    def discovery_time_series(self):
        return self.discovery.projects().timeSeries()

    @property
    def discovery_uptime_check(self):
        return self.discovery.projects().uptimeCheckConfigs()
