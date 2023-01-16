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

from google.oauth2 import service_account

from ..gcp import GoogleCloudPlatform

from .. import constants


class CloudResourcesBase(GoogleCloudPlatform):

    def __init__(self,
                 config,
                 logger,
                 name):

        super(CloudResourcesBase, self).__init__(
            config,
            logger,
            name=name,
            scope=constants.COMPUTE_SCOPE,
            discovery=constants.CLOUDRESOURCES_DISCOVERY,
            api_version=constants.API_V1)

    def get_credentials(self, *_, **__):
        return service_account.Credentials.\
            from_service_account_info(self.auth)

    def get(self):
        raise NotImplementedError()

    def create(self):
        raise NotImplementedError()

    def delete(self):
        raise NotImplementedError()
