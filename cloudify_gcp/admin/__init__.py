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

from oauth2client import GOOGLE_TOKEN_URI
from oauth2client.client import GoogleCredentials

from .. import gcp
from .. import constants


class CloudResourcesBase(gcp.GoogleCloudApi):

    def __init__(self,
                 config,
                 logger,
                 scope=constants.COMPUTE_SCOPE,
                 discovery=constants.CLOUDRESOURCES_DISCOVERY,
                 api_version=constants.API_V1):

        super(CloudResourcesBase, self).__init__(
            config,
            logger,
            scope,
            discovery,
            api_version)

    def get_credentials(self, scope):
        # check
        # run: gcloud beta auth application-default login
        # look to ~/.config/gcloud/application_default_credentials.json
        credentials = GoogleCredentials(
            access_token=None,
            client_id=self.auth['client_id'],
            client_secret=self.auth['client_secret'],
            refresh_token=self.auth['refresh_token'],
            token_expiry=None,
            token_uri=GOOGLE_TOKEN_URI,
            user_agent='Python client library'
        )
        return credentials

    def get(self):
        raise NotImplementedError()

    def create(self):
        raise NotImplementedError()

    def delete(self):
        raise NotImplementedError()
