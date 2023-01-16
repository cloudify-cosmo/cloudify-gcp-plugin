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

from cloudify.exceptions import NonRecoverableError

from cloudify_gcp.compute import snapshot
from ...tests import TestGCP


@patch('cloudify_gcp.utils.assure_resource_id_correct', return_value=True)
@patch('cloudify_gcp.gcp.service_account.Credentials.'
       'from_service_account_info')
@patch('cloudify_gcp.utils.get_gcp_resource_name', return_value='valid_name')
@patch('cloudify_gcp.gcp.build')
class TestGCPSnapshot(TestGCP):

    def test_create(self, mock_build, *args):
        mock_build().globalOperations().get().execute.side_effect = [
                {'status': 'PENDING', 'name': 'Dave'},
                {'status': 'DONE', 'name': 'Dave'},
                ]

        snapshot.create(disk_name='abc', snapshot_name='cde')

        mock_build().disks().createSnapshot.assert_called_once_with(
                body={
                    'name': 'valid_name',
                    'description': None
                    },
                disk='abc',
                project='not really a project',
                zone='a very fake zone'
                )

        # check no snapshot name
        with self.assertRaises(NonRecoverableError):
            snapshot.create(
                disk_name='abc')

    def test_create_incremental(self, mock_build, *args):
        # check incremental/skipped without error
        snapshot.create(
            disk_name='abc',
            snapshot_name='cde',
            snapshot_incremental=True)

        mock_build.assert_not_called()

    def test_delete(self, mock_build, *args):
        snapshot.delete(snapshot_name='cde')

        mock_build.assert_called_once()
        mock_build().snapshots().delete.assert_called_with(
                project='not really a project',
                snapshot='valid_name'
                )

        # check no snapshot name
        with self.assertRaises(NonRecoverableError):
            snapshot.delete()

    def test_delete_incremental(self, mock_build, *args):
        # check incremental/skipped without error
        snapshot.delete(
            snapshot_name='cde',
            snapshot_incremental=True)
        mock_build.assert_not_called()
