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
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from mock import patch, MagicMock

from .. import global_forwarding_rule
from ...tests import TestGCP


@patch('cloudify_gcp.utils.assure_resource_id_correct', return_value=True)
@patch('cloudify_gcp.gcp.ServiceAccountCredentials.from_json_keyfile_dict')
@patch('cloudify_gcp.utils.get_gcp_resource_name', return_value='valid_name')
@patch('cloudify_gcp.gcp.build')
class TestForwardingRule(TestGCP):

    def test_create(self, mock_build, *args):
        self.ctxmock.node.properties.update({
            'target_proxy': 'walmart',
            })
        global_forwarding_rule.create(
                name='name',
                target_proxy='target',
                port_range='range',
                ip_address='ip',
                additional_settings={},
                )

        mock_build.assert_called_once()
        mock_build().globalForwardingRules().insert.assert_called_with(
                body={
                    'portRange': 'range',
                    'IPAddress': 'ip',
                    'target': 'target',
                    'description': 'Cloudify generated Global Forwarding Rule',
                    'name': 'name'},
                project='not really a project'
                )

    @patch('cloudify_gcp.utils.response_to_operation')
    def test_delete(self, mock_response, mock_build, *args):
        self.ctxmock.instance.runtime_properties.update({
            'name': 'delete_name',
            })

        operation = MagicMock()
        operation.has_finished.return_value = True
        mock_response.return_value = operation

        global_forwarding_rule.delete()

        mock_build.assert_called_once()
        mock_build().globalForwardingRules().delete.assert_called_with(
                forwardingRule='delete_name',
                project='not really a project',
                )
