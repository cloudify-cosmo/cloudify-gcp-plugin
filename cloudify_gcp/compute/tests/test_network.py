########
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

from cloudify_gcp.compute import network
from ...tests import TestGCP


@patch('cloudify_gcp.gcp.ServiceAccountCredentials.from_json_keyfile_dict')
@patch('cloudify_gcp.gcp.build')
class TestGCPNetwork(TestGCP):

    def test_create(self, mock_build, *args):
        network.create(
                name='network-name',
                auto_subnets=True,
                additional_settings={},
                )

        mock_build().networks().insert.assert_called_once_with(
                body={
                    'description': 'Cloudify generated network',
                    'name': 'network-name',
                    'autoCreateSubnetworks': True,
                    },
                project='not really a project',
                )

    def test_delete(self, mock_build, *args):
        self.ctxmock.instance.runtime_properties.update({
                'name': 'hi',
                })

        network.delete('name')

        mock_build().networks().delete.assert_called_once_with(
                network='hi',
                project='not really a project',
                )
