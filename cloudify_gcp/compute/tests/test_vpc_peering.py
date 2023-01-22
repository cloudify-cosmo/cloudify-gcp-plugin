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

from cloudify_gcp.compute import network
from ...tests import TestGCP


@patch('cloudify_gcp.gcp.service_account.Credentials.'
       'from_service_account_info')
@patch('cloudify_gcp.gcp.build')
class TestGCPNetwork(TestGCP):

    def test_create(self, mock_build, *args):
        network.add_peering(
                name='name',
                network='network',
                peerNetwork='peerNetwork',
                autoCreateRoutes=False
                )

        mock_build().networks().addPeering.assert_called_once_with(
                body={
                    'name': 'name',
                    'peerNetwork': 'global/networks/peerNetwork',
                    'autoCreateRoutes': False},
                network='network',
                project='not really a project')

    def test_delete(self, mock_build, *args):
        self.ctxmock.instance.runtime_properties.update({
                'name': 'name',
                })

        network.remove_peering(
                name='name',
                network='network',
                peerNetwork='peerNetwork')

        mock_build().networks().removePeering.assert_called_once_with(
                network='network',
                project='not really a project',
                body={
                    'name': 'name'}
                )
