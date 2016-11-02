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

from cloudify.exceptions import NonRecoverableError

from .. import subnetwork
from ...tests import TestGCP


@patch('cloudify_gcp.gcp.ServiceAccountCredentials.from_json_keyfile_dict')
@patch('cloudify_gcp.gcp.build')
class TestGCPSubNetwork(TestGCP):

    def setUp(self):
        super(TestGCPSubNetwork, self).setUp()

        self.ctxmock.node.properties['region'] = 'Bukit Bintang'

    def test_create(self, mock_build, *args):
        rel = Mock()
        rel.type = 'cloudify.gcp.relationships.contained_in_network'
        rel.target.node.type = 'cloudify.gcp.nodes.Network'
        rel.target.node.properties = {
                'auto_subnets': False,
                }
        rel.target.instance.runtime_properties = {
                'selfLink': 'Look at me!',
                }
        self.ctxmock.instance.relationships.append(rel)
        self.ctxmock.node.properties.update({
            'use_external_resource': False,
            'subnet': 'Toki Tori',
            })

        subnetwork.create(
                name='subnet name',
                region='Bukit Bintang',
                subnet='Token Ring',
                )

        mock_build().subnetworks().insert.assert_called_once_with(
                body={
                    'ipCidrRange': 'Token Ring',
                    'network': 'Look at me!',
                    'name': 'subnetname',
                    'description': 'Cloudify generated subnetwork',
                    },
                project='not really a project',
                region='Bukit Bintang',
                )

    def test_create_validation(self, mock_build, *args):
        with self.assertRaises(NonRecoverableError) as e:
            subnetwork.create(
                    name='network-name',
                    )
        self.assertIn(
                'cloudify.gcp.relationships.contained_in_network',
                e.exception.message)

    def test_create_auto_validate(self, mock_build, *args):
        rel = Mock()
        rel.type = 'cloudify.gcp.relationships.contained_in_network'
        rel.target.node.type = 'cloudify.gcp.nodes.Network'
        rel.target.node.properties = {
                'auto_subnets': True,
                }
        rel.target.instance.runtime_properties = {
                'selfLink': 'Look at me!',
                }
        self.ctxmock.instance.relationships.append(rel)
        self.ctxmock.node.properties['use_external_resource'] = False

        with self.assertRaises(NonRecoverableError) as e:
            subnetwork.create(
                    name='subnet name',
                    region='Bukit Bintang',
                    subnet='Token Ring',
                    )
        self.assertIn(
                'auto_subnets',
                e.exception.message)

    def test_delete(self, mock_build, *args):
        self.ctxmock.instance.runtime_properties = {
                'name': 'hi',
                'region': 'Gondor',
                }

        subnetwork.delete()

        mock_build().subnetworks().delete.assert_called_once_with(
                project='not really a project',
                region='Gondor',
                subnetwork='hi'
                )
