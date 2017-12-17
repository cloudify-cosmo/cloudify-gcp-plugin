# -*- coding: utf-8 -*-
########
# Copyright (c) 2017 GigaSpaces Technologies Ltd. All rights reserved
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

# Local imports
from __future__ import unicode_literals

# Third-party imports
from mock import patch

# Local imports
from cloudify_gcp.container_engine import cluster
from ...tests import TestGCP


@patch('cloudify_gcp.utils.assure_resource_id_correct', return_value=True)
@patch('cloudify_gcp.gcp.ServiceAccountCredentials.from_json_keyfile_dict')
@patch('cloudify_gcp.utils.get_gcp_resource_name', return_value='valid_name')
@patch('cloudify_gcp.gcp.build')
class TestGCPCluster(TestGCP):

    def test_create(self, mock_build, *args):
        cluster.create('valid_name', additional_settings={}, )

        mock_build().projects().zones().clusters(

        ).create.assert_called_once_with(
                body={'cluster': {'name': 'valid_name',
                                  'initialNodeCount': 1}, },
                projectId='not really a project',
                zone='a very fake zone')

    def test_start(self, mock_build, *args):
        self.ctxmock.instance.runtime_properties['name'] = 'valid_name'
        cluster.start()
        mock_build.assert_called_once()

    def test_delete(self, mock_build, *args):
        self.ctxmock.instance.runtime_properties['name'] = 'valid_name'
        cluster.delete()
        mock_build.assert_called_once()

    def test_stop(self, mock_build, *args):
        self.ctxmock.instance.runtime_properties['name'] = 'valid_name'

        cluster.stop()

        mock_build.assert_called_once()

        mock_build().projects().zones().clusters().delete.assert_called_with(
            clusterId='valid_name',
            projectId='not really a project',
            zone='a very fake zone')
