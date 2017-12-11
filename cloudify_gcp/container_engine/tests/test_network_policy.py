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

# Local imports
from __future__ import unicode_literals

# Third-party imports
from mock import patch
from cloudify import ctx

# Local imports
from cloudify_gcp.container_engine import network_policy
from ...tests import TestGCP


@patch('cloudify_gcp.utils.assure_resource_id_correct', return_value=True)
@patch('cloudify_gcp.gcp.ServiceAccountCredentials.from_json_keyfile_dict')
@patch('cloudify_gcp.utils.get_gcp_resource_name', return_value='valid_name')
@patch('cloudify_gcp.gcp.build')
class TestGCPNetworkPolicy(TestGCP):

    def test_create_policy_addon(self, mock_build, *args):
        network_policy.enable_network_policy_addon('valid_name')
        mock_build().projects().zones().clusters(
        ).update.assert_called_once_with(
            body={
                'update': {
                    'desiredAddonsConfig': {
                        'networkPolicyConfig': {
                            'disabled': False
                        }
                    }
                }
            },
            projectId='not really a project',
            zone='a very fake zone',
            clusterId='valid_name')

        self.assertEqual(
            ctx.instance.runtime_properties['cluster_id'],
            'valid_name')

    def test_delete_policy_addon(self, mock_build, *args):
        ctx.instance.runtime_properties['cluster_id'] = 'valid_name'
        network_policy.disable_network_policy_addon()

        mock_build.assert_called_once()
        mock_build().projects().zones().clusters(
        ).update.assert_called_once_with(
            body={
                'update': {
                    'desiredAddonsConfig': {
                        'networkPolicyConfig': {
                            'disabled': True
                        }
                    }
                }
            },
            projectId='not really a project',
            zone='a very fake zone',
            clusterId='valid_name')

    def test_create_policy_config(self, mock_build, *args):
        ctx.instance.runtime_properties['cluster_id'] = 'valid_name'
        network_policy.create_network_policy_config(
            {'provider': 'test-provider', 'enabled': True},
            additional_settings={}
        )

        mock_build().projects().zones().clusters(
        ).setNetworkPolicy.assert_called_once_with(
            body={'networkPolicy': {'provider': 'test-provider',
                                    'enabled': True}},
            projectId='not really a project',
            zone='a very fake zone',
            clusterId='valid_name')

    def test_delete_policy_config(self, mock_build, *args):
        ctx.instance.runtime_properties['cluster_id'] = 'valid_name'
        network_policy.delete_network_policy_config()

        mock_build.assert_called_once()

        mock_build().projects().zones().clusters(
        ).setNetworkPolicy.assert_called_once_with(
            body={'networkPolicy': {'provider': 'PROVIDER_UNSPECIFIED',
                                    'enabled': False}},
            projectId='not really a project',
            zone='a very fake zone',
            clusterId='valid_name')
