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

from cloudify_gcp.compute import security_group
from ...tests import TestGCP


@patch('cloudify_gcp.utils.assure_resource_id_correct', return_value=True)
@patch('cloudify_gcp.gcp.ServiceAccountCredentials.from_json_keyfile_dict')
@patch('cloudify_gcp.gcp.build')
class TestGCPSecurityGroup(TestGCP):

    def setUp(self):
        super(TestGCPSecurityGroup, self).setUp()
        self.ctxmock.instance.relationships = []

    def test_create(self, mock_build, *args):
        self.ctxmock.node.properties['rules'] = rules = [
                    {
                        'allowed': {'NOTHING!': ''},
                        'sources': ['bob', 'jane'],
                    },
                    {
                        'allowed': {'tcp': ['40', 41]},
                        'sources': ['jane'],
                    },
                ]

        security_group.create(
                'name',
                rules,
                )

        self.assertEqual(2, mock_build.call_count)
        for body in [
                {
                    'network': 'projects/not really a project/'
                               'global/networks/not a real network',
                    'sourceTags': ['bob', 'jane'],
                    'description': 'Cloudify generated SG part',
                    'sourceRanges': [],
                    'targetTags': ['ctx-sg-name'],
                    'allowed': [{'IPProtocol': 'NOTHING!'}],
                    'name': 'ctx-sg-name-from-bobjane-to-nothing',
                },
                {
                    'network': 'projects/not really a project/'
                               'global/networks/not a real network',
                    'sourceTags': ['jane'],
                    'description': 'Cloudify generated SG part',
                    'sourceRanges': [],
                    'targetTags': ['ctx-sg-name'],
                    'allowed': [{
                        'IPProtocol': 'tcp',
                        'ports': ['40', 41]}],
                    'name': 'ctx-sg-name-from-jane-to-tcp4041',
                },
                ]:

            mock_build().firewalls().insert.assert_any_call(
                    body=body,
                    project='not really a project'
                    )

    def test_delete(self, mock_build, *args):
        props = self.ctxmock.instance.runtime_properties
        props['gcp_name'] = 'delete_name'
        props['rules'] = [
                {'name': 'You do not talk about Fight Club'},
                {'name': 'You DO NOT talk about Fight Club'},
                ]

        security_group.delete()

        self.assertEqual(2, mock_build.call_count)
        mock_build().firewalls().delete.assert_called_with(
                firewall='youdonottalkaboutfightclub',
                project='not really a project',
                )
