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
#    * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    * See the License for the specific language governing permissions and
#    * limitations under the License.

from mock import Mock, patch

from cloudify_gcp.compute import route
from ...tests import TestGCP


@patch('cloudify_gcp.gcp.ServiceAccountCredentials.from_json_keyfile_dict')
@patch('cloudify_gcp.gcp.build')
class TestGCPRoute(TestGCP):

    def test_create(self, mock_build, *args):

        route.create(
                'dest_range',
                'name',
                'tags',
                'next_hop',
                'priority',
                )

        mock_build().routes().insert.assert_called_once_with(
                body={
                    'network': 'projects/not really a project/'
                               'global/networks/not a real network',
                    'tags': 'tags',
                    'name': 'name',
                    'priority': 'priority',
                    'destRange': 'dest_range',
                    'nextHopIp': 'next_hop',
                    'description': 'Cloudify generated route'
                    },
                project='not really a project',
                )

    def test_create_default_gateway(self, mock_build, *args):

        route.create(
                'dest_range',
                'name',
                'tags',
                priority='priority',
                next_hop='',
                )

        mock_build().routes().insert.assert_called_once_with(
            body={
                'nextHopGateway': 'global/gateways/default-internet-gateway',
                'network': 'projects/not really a project/'
                           'global/networks/not a real network',
                'tags': 'tags',
                'name': 'name',
                'priority': 'priority',
                'destRange': 'dest_range',
                'description': 'Cloudify generated route'
                },
            project='not really a project',
            )

    def test_create_with_instance(self, mock_build, *args):
        rel_mock = Mock()
        rel_mock.target.instance.runtime_properties = {
                'kind': 'an#instance',
                'selfLink': 'I am pointing to ///instances/instanceName',
                }
        self.ctxmock.instance.relationships.append(rel_mock)

        route.create(
                'dest_range',
                'name',
                'tags',
                priority='priority',
                next_hop='',
                )

        mock_build().routes().insert.assert_called_once_with(
                body={
                    'network': 'projects/not really a project/'
                               'global/networks/not a real network',
                    'tags': 'tags',
                    'name': 'name',
                    'priority': 'priority',
                    'destRange': 'dest_range',
                    'nextHopInstance':
                        'I am pointing to ///instances/instanceName',
                    'description': 'Cloudify generated route'
                    },
                project='not really a project',
                )

    def test_delete(self, mock_build, *args):
        self.ctxmock.instance.runtime_properties.update({
                'name': 'hi',
                })

        route.delete('name')

        mock_build().routes().delete.assert_called_once_with(
                route='hi',
                project='not really a project',
                )
