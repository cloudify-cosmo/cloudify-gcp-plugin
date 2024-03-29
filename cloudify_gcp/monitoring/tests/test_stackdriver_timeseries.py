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

# Local imports
from __future__ import unicode_literals

# Third-party imports
from mock import patch

# Local imports
from .. import stackdriver_timeseries
from ...tests import TestGCP


@patch('cloudify_gcp.gcp.service_account.Credentials.'
       'from_service_account_info')
@patch('cloudify_gcp.gcp.build')
class TestGCPStackDriverTimeSeries(TestGCP):

    def test_create(self, mock_build, *args):
        dummy_dict = {'a': 1, 'b': "2"}
        stackdriver_timeseries.create(
            project_id='proj-id', time_series=dummy_dict)

        mock_build().projects().timeSeries().create.assert_called_once_with(
            name='projects/proj-id', body=dummy_dict
        )
