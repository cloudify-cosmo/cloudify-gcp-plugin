# #######
# Copyright (c) 2016 GigaSpaces Technologies Ltd. All rights reserved
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

from cloudify.manager import DirtyTrackingDict

from .. import instance_group
from ...tests import TestGCP


@patch('cloudify_gcp.gcp.ServiceAccountCredentials.from_json_keyfile_dict')
@patch('cloudify_gcp.gcp.build')
class TestInstanceGroup(TestGCP):

    def setUp(self):
        super(TestInstanceGroup, self).setUp()
        self.ctxmock.source.instance.runtime_properties = DirtyTrackingDict()

    def test_create(self, mock_build, *args):
        instance_group.create(
                'name',
                ['port', 83],
                additional_settings={},
                )

        mock_build().instanceGroups().insert.assert_called_once_with(
                body={
                    'network': 'global/networks/not a real network',
                    'namedPorts': ['port', 83],
                    'description': 'Cloudify generated instance group',
                    'name': 'name'},
                project='not really a project',
                zone='a very fake zone'
                )

    def test_delete(self, mock_build, *args):
        self.ctxmock.instance.runtime_properties['name'] = 'delete me'

        instance_group.delete()

        mock_build().instanceGroups().delete.assert_called_once_with(
                instanceGroup='delete me',
                project='not really a project',
                zone='a very fake zone',
                )

    def test_add_to_instance_group(self, mock_build, *args):
        mock_build().globalOperations().get().execute.side_effect = [
                {'status': 'PENDING', 'name': 'Dave'},
                {'status': 'DONE', 'name': 'Dave'},
                ]

        instance_group.add_to_instance_group('group name', 'instance url')

        mock_build().instanceGroups().addInstances.assert_called_once_with(
                body={
                    'instances': [
                        {'instance': 'instance url'}]},
                instanceGroup='group name',
                project='not really a project',
                zone='a very fake zone'
                )

    def test_remove_from_instance_group(self, mock_build, *args):
        mock_build().globalOperations().get().execute.side_effect = [
                {'status': 'PENDING', 'name': 'Dave'},
                {'status': 'DONE', 'name': 'Dave'},
                ]

        instance_group.remove_from_instance_group(
                'group name', 'instance url')

        mock_build().instanceGroups().removeInstances.assert_called_once_with(
                body={
                    'instances': [
                        {'instance': 'instance url'}]},
                instanceGroup='group name',
                project='not really a project',
                zone='a very fake zone'
                )
