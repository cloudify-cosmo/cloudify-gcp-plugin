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
from __future__ import unicode_literals

from cloudify_gcp import constants
from cloudify_gcp.gcp import check_response
from cloudify_gcp.gcp import GoogleCloudPlatform


class IAMBase(GoogleCloudPlatform):
    def __init__(self,
                 config,
                 logger,
                 name,
                 additional_settings=None):
        """
         Kubernetes Engine Base Class

        :param config:
        :param logger:
        :param name: name of the kubernetes resource, if None project name
        will be taken
        """
        super(IAMBase, self).\
            __init__(config, logger,
                     name, additional_settings,
                     scope=constants.IAM_SCOPE,
                     discovery=constants.IAM_DISCOVERY)
        self.name = self.name if name else self.project

    @check_response
    def create(self):
        raise NotImplementedError()

    def to_dict(self):
        raise NotImplementedError()

    @check_response
    def delete(self):
        raise NotImplementedError()
