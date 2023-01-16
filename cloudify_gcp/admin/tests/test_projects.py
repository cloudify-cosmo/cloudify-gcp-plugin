########
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

from ...tests import TestGCP
from cloudify_gcp.admin import projects


class TestProjectsWithCTX(TestGCP):

    def _set_properties(self):
        self.ctxmock.node.properties = {
            "gcp_config": {
                "auth": {
                    "client_id": "client_id",
                    "client_secret": "client_secret",
                    "refresh_token": "refresh_token"
                }
            },
            "name:": "project_name",
            "id": "project_id"
        }

    def test_project_init(self):
        self._set_properties()
        config = self.ctxmock.node.properties["gcp_config"]
        parent = {'type': 'organization', 'id': '840516624432'}

        project_check = projects.Project(config,
                                         self.ctxmock.logger,
                                         "abc",
                                         "project_id",
                                         parent)

        self.assertEqual(project_check.config, config)
        self.assertEqual(project_check.name, "abc")
        self.assertEqual(project_check.project_id, "project_id")

        project_check = projects.Project(config, self.ctxmock.logger, "abc")
        self.assertEqual(project_check.config, config)
        self.assertEqual(project_check.name, "abc")
        self.assertEqual(project_check.project_id, "abc")
