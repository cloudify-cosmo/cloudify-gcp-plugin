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

# Local imports
from cloudify_gcp import constants
from cloudify_gcp.gcp import check_response
from cloudify_gcp.gcp import GoogleCloudPlatform


class MonitoringBase(GoogleCloudPlatform):
    def __init__(self,
                 config,
                 logger,
                 name,
                 additional_settings=None):
        """
         Monitoring Base Class
        :param config: dictionary with project properties: path to auth file,
        project and zone
        :param logger: logger object that the class methods will be logging to
        """
        super(MonitoringBase, self).\
            __init__(config, logger,
                     additional_settings,
                     scope=constants.MONITORING_SCOPE,
                     discovery=constants.MONITORING_DISCOVERY,
                     api_version=constants.API_V3, )

        self.name = name if name else self.project

    @check_response
    def create(self):
        raise NotImplementedError()

    def to_dict(self):
        raise NotImplementedError()

    @check_response
    def delete(self):
        raise NotImplementedError()

    @property
    def discovery_monitoring(self):
        return self.discovery.projects() if self.discovery else None
