#!/usr/bin/env python
# -*- coding: utf-8 -*-
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

from mock import patch

from cloudify_gcp.compute import url_map
from ...tests import TestGCP


@patch('cloudify_gcp.utils.assure_resource_id_correct', return_value=True)
@patch('cloudify_gcp.gcp.ServiceAccountCredentials.from_json_keyfile_dict')
@patch('cloudify_gcp.utils.get_gcp_resource_name', return_value='valid_name')
@patch('cloudify_gcp.gcp.build')
class TestUrlMap(TestGCP):

    def test_create(self, mock_build, *args):
        self.ctxmock.node.properties['default_service'] = 'default service'

        url_map.create(
                'name',
                'default service',
                )

        mock_build.assert_called_once()
        mock_build().urlMaps().insert.assert_called_with(
                body={
                    'name': 'name',
                    'description': 'Cloudify generated URL Map',
                    'defaultService': 'default service'},
                project='not really a project'
                )

    @patch('cloudify_gcp.utils.response_to_operation')
    def test_delete(self, mock_response, mock_build, *args):
        self.ctxmock.instance.runtime_properties.update({
            'name': 'delete_name',
            })

        url_map.delete()

        mock_build.assert_called_once()
        mock_build().urlMaps().delete.assert_called_with(
                project='not really a project',
                urlMap='delete_name'
                )
