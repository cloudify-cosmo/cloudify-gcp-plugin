# -*- coding: utf-8 -*-
########
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

# Local imports
from __future__ import unicode_literals

# Third-party imports
from mock import patch
import mock

# Local imports
from cloudify.exceptions import OperationRetry

from cloudify_gcp.iam import role
from ...tests import TestGCP


@patch('cloudify_gcp.utils.assure_resource_id_correct', return_value=True)
@patch('cloudify_gcp.gcp.service_account.Credentials.'
       'from_service_account_info')
@patch('cloudify_gcp.utils.get_gcp_resource_name', return_value='valid_name')
@patch('cloudify_gcp.gcp.build')
class TestGCPRole(TestGCP):

    def test_create(self, mock_build, *_):
        role.create('valid_name', 'foo', 'bar', 'baz', 'taco')

        mock_build().projects().roles().create.assert_called_once_with(
            parent='projects/not really a project',
            body={'roleId': 'valid_name',
                  'role': {
                      'title': 'foo',
                      'description': 'bar',
                      'includedPermissions': 'baz',
                      'stage': 'taco'
                      }
                  })

    def test_delete(self, mock_build, *_):

        self.ctxmock.instance.runtime_properties['name'] = 'valid_name'
        roles = mock_build().projects().roles().get().execute()

        # stopping
        self.ctxmock.operation.retry = mock.Mock()
        roles.get = mock.Mock(return_value={})
        with self.assertRaises(OperationRetry):
            role.delete()
        # self.ctxmock.operation.retry.assert_called_with(
        #     role.DELETING_MESSAGE.format(deleted=None))

        self.ctxmock.operation.retry = mock.Mock()
        roles.get = mock.Mock(return_value=role.DELETING_MESSAGE.format(
            deleted=True))
        role.delete()
