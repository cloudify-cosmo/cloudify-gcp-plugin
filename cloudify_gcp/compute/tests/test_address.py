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
#    * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    * See the License for the specific language governing permissions and
#    * limitations under the License.

from mock import patch

from .. import address
from ...tests import TestGCP


@patch('cloudify_gcp.gcp.ServiceAccountCredentials.from_json_keyfile_dict')
@patch('cloudify_gcp.gcp.build')
class TestAddress(TestGCP):

    def setUp(self):
        super(TestAddress, self).setUp()

        self.ctxmock.node.properties['gcp_config']['zone'] = 'us-central1-b'

    def test_create(self, mock_build, *args):
        address.create(
                'name',
                additional_settings={},
                region='region',
                )

        mock_build().addresses().insert.assert_called_once_with(
                body={
                    'description': 'Cloudify generated Address',
                    'name': 'name',
                    },
                project='not really a project',
                region='region',
                )

    def test_delete(self, mock_build, *args):
        self.ctxmock.instance.runtime_properties.update({
            'gcp_name': 'delete me',
            'region': 'Costa Del Sol',
            'name': 'delete me',
            })

        address.delete()

        mock_build().addresses().delete.assert_called_once_with(
                project='not really a project',
                address='delete me',
                region='Costa Del Sol',
                )

    def test_create_global(self, mock_build, *args):
        address.create('name', '')

        mock_build().globalAddresses().insert.assert_called_once_with(
                body={
                    'description': 'Cloudify generated Address',
                    'name': 'name',
                    },
                project='not really a project',
                )

    def test_delete_global(self, mock_build, *args):
        self.ctxmock.instance.runtime_properties.update({
            'name': 'delete me',
            })

        address.delete()

        mock_build().globalAddresses().delete.assert_called_once_with(
                project='not really a project',
                address='delete me',
                )
