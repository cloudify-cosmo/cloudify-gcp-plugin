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

from .. import constants
from .. import utils
from ..gcp import (
    check_response,
    GoogleCloudPlatform,
    )


class PubSubBase(GoogleCloudPlatform):
    def __init__(self,
                 config,
                 logger,
                 name,
                 additional_settings=None,
                 ):
        """
        Create PubSub object

        :param config: gcp auth file
        :param logger: logger object
        :param name: name for the PubSub resoruce

        """
        super(PubSubBase, self).__init__(
            config,
            logger,
            utils.get_gcp_resource_name(name),
            discovery=constants.PUB_SUB_DISCOVERY,
            scope=constants.PUB_SUB_SCOPE,
            additional_settings=additional_settings,
            )
        self.name = name

    @check_response
    def create(self):
        raise NotImplementedError()

    @check_response
    def delete(self):
        raise NotImplementedError()

    @property
    def discovery_pubsub(self):
        return self.discovery.projects() if self.discovery else None
