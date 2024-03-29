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

from mock import patch

from cloudify_gcp.compute import region_backend_service
from ...tests import TestGCP


@patch('cloudify_gcp.utils.assure_resource_id_correct', return_value=True)
@patch('cloudify_gcp.gcp.service_account.Credentials.'
       'from_service_account_info')
@patch('cloudify_gcp.utils.get_gcp_resource_name', return_value='valid_name')
@patch('cloudify_gcp.gcp.build')
class TestGCPBackendService(TestGCP):

    def test_create(self, mock_build, *args):
        region_backend_service.create(
                'name',
                "region",
                'health check',
                'tcp',
                additional_settings={},
                )

        mock_build.assert_called_once()
        mock_build().regionBackendServices().insert.assert_called_with(
                body={
                    'healthChecks': ['health check'],
                    'protocol': 'tcp',
                    'description': 'Cloudify generated backend service',
                    'name': 'name'},
                project='not really a project',
                region='region'
                )

    def test_delete(self, mock_build, *args):
        self.ctxmock.instance.runtime_properties.update({
                'name': 'delete_name',
                'region': 'region',
                })

        region_backend_service.delete()

        mock_build().regionBackendServices().delete.assert_called_once_with(
                backendService='delete_name',
                project='not really a project',
                region='region'
                )

    def test_add_backend(self, mock_build, *args):
        mock_build().globalOperations().get().execute.side_effect = [
                {'status': 'PENDING', 'name': 'Dave'},
                {'status': 'DONE', 'name': 'Dave'},
                {'status': 'DONE', 'name': 'Harry'},
                ]
        self.ctxmock.source.instance.runtime_properties = {
                'backends': [],
                'region': "region",
                }

        mock_build().regionBackendServices().get().execute.return_value = {
                    'backends': [
                        {'group': 'group'},
                    ],
                }

        region_backend_service.add_backend('backend_name', 'group')

        region_backend_service.add_backend('backend_name', 'group 2')

        mock_build().regionBackendServices().patch.assert_called_with(
                backendService='backend_name',
                body={'backends': [
                    {'group': 'group'},
                    {'group': 'group 2'},
                    ]},
                project='not really a project',
                region='region'
                )

    def test_remove_backend(self, mock_build, *args):
        mock_build().globalOperations().get().execute.side_effect = [
                {'status': 'PENDING', 'name': 'Boris'},
                {'status': 'DONE', 'name': 'Boris'},
                ]
        self.ctxmock.source.instance.runtime_properties = {
                'region': "region",
                'backends': [
                    {'group': 'group 1'},
                    {'group': 'group 2'},
                    {'group': 'group 3'},
                    ],
                }

        region_backend_service.remove_backend(
                'backend_name',
                'group 1',
                )

        mock_build().regionBackendServices().patch.assert_called_once_with(
                backendService='backend_name',
                body={'backends': [
                    {'group': 'group 2'},
                    {'group': 'group 3'},
                    ]},
                project='not really a project',
                region='region'
                )
