# -*- coding: utf-8 -*-
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

from cloudify.exceptions import NonRecoverableError

# Local imports
from .. import exclusion
from ...tests import TestGCP


@patch('cloudify_gcp.utils.assure_resource_id_correct', return_value=True)
@patch('cloudify_gcp.gcp.ServiceAccountCredentials.from_json_keyfile_dict')
@patch('cloudify_gcp.utils.get_gcp_resource_name', return_value='valid_name')
@patch('cloudify_gcp.gcp.build')
class TestLoggingExclusion(TestGCP):
    def test_create(self, mock_build, *args):
        exclusion.create(self.ctxmock, parent='folders/test-proj',
                         log_exclusion={'key1': 'value1', 'key2': 'value2'},
                         exclusion_type='Folder')

        mock_build().folders().exclusions().create.assert_called_once_with(
            body={'key1': 'value1', 'key2': 'value2'},
            parent='folders/test-proj')

    def test_invalid_type_creation(self, mock_build, *args):
        with self.assertRaises(NonRecoverableError):
            exclusion.create(self.ctxmock, parent='folders/test-proj',
                             log_exclusion={
                                 'key1': 'value1', 'key2': 'value2'},
                             exclusion_type='wrong-type')
        mock_build.folders().exclusions().create.assert_not_called()

    def test_delete(self, mock_build, *args):
        self.ctxmock.instance.runtime_properties['name'] = 'dummy-name'
        exclusion.delete(exclusion_type='Folder')

        mock_build().folders().exclusions().delete.assert_called_once_with(
            name='dummy-name')
