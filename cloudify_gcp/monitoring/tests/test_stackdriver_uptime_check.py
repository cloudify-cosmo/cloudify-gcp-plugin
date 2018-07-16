########
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

# Local imports
from __future__ import unicode_literals

# Third-party imports
from mock import patch

# Local imports
from .. import stackdriver_uptimecheck
from ...tests import TestGCP


@patch('cloudify_gcp.gcp.build')
class TestGCPStackDriverGCP(TestGCP):

    def test_create(self, mock_build, *args):
        test_dict = {'a': 1, 'bb': 2, 'cc': 'cc', }
        stackdriver_uptimecheck.create(
            project_id='proj-id', uptime_check_config=test_dict)

        mock_build().projects().uptimeCheckConfigs(
        ).create.assert_called_once_with(
            parent='projects/proj-id', body=test_dict)

    def test_delete(self, mock_build, *args):
        self.ctxmock.instance.runtime_properties['name'] = 'some-name'
        stackdriver_uptimecheck.delete()

        mock_build().projects().uptimeCheckConfigs(
        ).delete.assert_called_once_with(name='some-name')

    def test_update(self, mock_build, *args):
        self.ctxmock.instance.runtime_properties['name'] = 'some-name'
        test_dict = {'a': 1, 'bb': 2, 'cc': 'cc', }
        stackdriver_uptimecheck.update(
            project_id='proj-id', uptime_check_config=test_dict)

        mock_build().projects().uptimeCheckConfigs(
        ).update.assert_called_once_with(name='some-name', body=test_dict)
