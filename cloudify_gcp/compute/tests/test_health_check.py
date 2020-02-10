# -*- coding: utf-8 -*-
########
# Copyright (c) 2016-2020 Cloudify Platform Ltd. All rights reserved
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

import unittest

from mock import patch, MagicMock

from cloudify.exceptions import NonRecoverableError

from .. import health_check
from ...tests import TestGCP


@patch('cloudify_gcp.utils.assure_resource_id_correct', return_value=True)
@patch('cloudify_gcp.gcp.ServiceAccountCredentials.from_json_keyfile_dict')
@patch('cloudify_gcp.utils.get_gcp_resource_name', return_value='valid_name')
@patch('cloudify_gcp.gcp.build')
class TestHealthCheck(TestGCP):

    def test_create_http(self, mock_build, *args):
        health_check.create(
                'name',
                'http',
                None,
                {},
                )

        mock_build.assert_called_once()
        mock_build().httpHealthChecks().insert.assert_called_with(
                body={
                    'description': 'Cloudify generated httpHealthCheck',
                    'name': 'name'},
                project='not really a project'
                )

    def test_create_https(self, mock_build, *args):
        health_check.create(
                'name',
                'https',
                None,
                {},
                )

        mock_build.assert_called_once()
        mock_build().httpsHealthChecks().insert.assert_called_with(
                body={
                    'description': 'Cloudify generated httpsHealthCheck',
                    'name': 'name'},
                project='not really a project'
                )

    def test_create_tcp(self, mock_build, *args):
        health_check.create(
                'name',
                'tcp',
                110,
                {},
                )

        mock_build.assert_called_once()
        mock_build().healthChecks().insert.assert_called_with(
                body={
                    'description': 'Cloudify generated healthCheck',
                    'tcpHealthCheck': {'port': 110},
                    'type': 'TCP',
                    'name': 'name'},
                project='not really a project'
                )

    def test_create_ssl(self, mock_build, *args):
        health_check.create(
                'name',
                'ssl',
                110,
                {},
                )

        mock_build.assert_called_once()
        mock_build().healthChecks().insert.assert_called_with(
                body={
                    'description': 'Cloudify generated healthCheck',
                    'sslHealthCheck': {'port': 110},
                    'type': 'SSL',
                    'name': 'name'},
                project='not really a project'
                )

    @patch('cloudify_gcp.utils.response_to_operation')
    def test_delete(self, mock_response, mock_build, *args):
        self.ctxmock.instance.runtime_properties.update({
            'name': 'delete_name',
            'kind': 'compute#httpHealthCheck',
            })

        operation = MagicMock()
        operation.has_finished.return_value = True
        mock_response.return_value = operation

        health_check.delete('http')

        mock_build.assert_called_once()
        mock_build().httpHealthChecks().delete.assert_called_with(
                httpHealthCheck='delete_name',
                project='not really a project',
                )


class TestHealthCheckHelpers(unittest.TestCase):

    def test_health_check_of_type_raises(self):
        with self.assertRaises(NonRecoverableError) as e:
            health_check.health_check_of_type('carrots')

        self.assertIn('Unexpected type', e.exception.message)
