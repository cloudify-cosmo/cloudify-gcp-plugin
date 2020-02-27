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
from cloudify_gcp.gcp import GoogleCloudPlatform
from .. import constants


class BillingAccountBase(GoogleCloudPlatform):
    def __init__(self, config, logger, name,
                 additional_settings=None,
                 scope=(constants.LOGGING_SCOPE, constants.CONTAINER_SCOPE),
                 discovery=constants.LOGGING_DISCOVERY,
                 api_version=constants.API_V2):
        super(BillingAccountBase, self).__init__(
            config, logger, name,
            additional_settings, scope, discovery, api_version)
