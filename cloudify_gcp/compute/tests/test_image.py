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

from cloudify_gcp.compute import image
from ...tests import TestGCP


@patch('cloudify_gcp.utils.assure_resource_id_correct', return_value=True)
@patch('cloudify_gcp.gcp.ServiceAccountCredentials.from_json_keyfile_dict')
@patch('cloudify_gcp.utils.get_gcp_resource_name', return_value='valid_name')
@patch('cloudify_gcp.gcp.build')
class TestGCPimage(TestGCP):

    @patch('cloudify_gcp.compute.image.Object')
    def test_create(self, mock_Object, mock_build, *args):
        image.create(
                'name',
                'path',
                additional_settings={},
                )

        mock_Object.assert_called_once_with(
                {'project': 'not really a project',
                    'zone': 'a very fake zone',
                    'auth': {
                        'client_email': 'nobody@invalid',
                        'private_key': 'nope!',
                        'type': 'service_account',
                        'private_key_id': "This isn't even an ID!",
                        },
                    'network': 'not a real network'
                 },
                self.ctxmock.logger.getChild(),
                'name.tar.gz',
                )

    def test_delete(self, mock_build, *args):
        self.ctxmock.instance.runtime_properties['name'] = 'delete_name'

        image.delete()

        mock_build.assert_called_once()
        mock_build().images().delete.assert_called_with(
                image='delete_name',
                project='not really a project',
                )
