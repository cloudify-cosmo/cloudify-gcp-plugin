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

from cloudify_gcp.compute import disk
from ...tests import TestGCP


@patch('cloudify_gcp.utils.assure_resource_id_correct', return_value=True)
@patch('cloudify_gcp.gcp.service_account.Credentials.'
       'from_service_account_info')
@patch('cloudify_gcp.utils.get_gcp_resource_name', return_value='valid_name')
@patch('cloudify_gcp.gcp.build')
class TestGCPDisk(TestGCP):

    def test_create(self, mock_build, *args):
        mock_build().globalOperations().get().execute.side_effect = [
                {'status': 'PENDING', 'name': 'Dave'},
                {'status': 'DONE', 'name': 'Dave'},
                ]

        disk.create(
                'image', 'name', 'size',
                boot=False,
                additional_settings={},
                )

        mock_build().disks().insert.assert_called_once_with(
                body={
                    'sourceImage': 'image',
                    'description': 'Cloudify generated disk',
                    'sizeGb': 'size',
                    'name': 'name'},
                project='not really a project',
                zone='a very fake zone',
                )

        # run one more time for check rerun
        disk.create(
                'image', 'name', 'size',
                boot=False,
                additional_settings={},
                )

    def test_delete(self, mock_build, *args):
        self.ctxmock.instance.runtime_properties['name'] = 'delete_name'

        disk.delete()

        mock_build.assert_called_once()
        mock_build().disks().delete.assert_called_with(
                disk='delete_name',
                project='not really a project',
                zone='a very fake zone',
                )

    def test_add_boot_disk(self, *args):
        self.ctxmock.source.instance.runtime_properties = {}
        self.ctxmock.target.instance.runtime_properties = {
                'gcp_disk': {},
                }

        disk.add_boot_disk()

        self.assertEqual(
                True,
                self.ctxmock.target.instance.runtime_properties[
                    'gcp_disk']['boot'])

        self.assertIs(
                self.ctxmock.target.instance.runtime_properties['gcp_disk'],
                self.ctxmock.source.instance.runtime_properties['gcp_disk'])

    def test_resize(self, mock_build, *args):
        mock_build().globalOperations().get().execute.side_effect = [
                {'status': 'PENDING', 'name': 'Dave'},
                {'status': 'DONE', 'name': 'Dave'},
        ]

        test_name = 'test_name'
        test_zone = 'test_zone'
        test_size = '40'

        mock_build().disks().resize().execute.return_value = {
                'id': 'fake_id',
                'name': test_name
        }

        disk.resize(test_name, test_zone, test_size)

        mock_build().disks().resize.assert_called_with(
                project='not really a project',
                zone='a very fake zone',
                disk=test_name,
                body={'sizeGb': test_size},
        )
