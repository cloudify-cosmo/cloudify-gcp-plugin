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

from cloudify_gcp.compute import firewall
from ...tests import TestGCP


@patch('cloudify_gcp.utils.assure_resource_id_correct', return_value=True)
@patch('cloudify_gcp.gcp.ServiceAccountCredentials.from_json_keyfile_dict')
@patch('cloudify_gcp.gcp.build')
class TestGCPFirewall(TestGCP):

    def setUp(self):
        super(TestGCPFirewall, self).setUp()
        self.ctxmock.instance.relationships = []

    def test_create(self, mock_build, *args):
        firewall.create(
                'name',
                allowed={'tcp': 'pct'},
                sources=['1', 'sauce'],
                target_tags=None,
                additional_settings={},
                )

        mock_build.assert_called_once()
        mock_build().firewalls().insert.assert_called_with(
                body={
                    'network': 'not a real network',
                    'sourceTags': ['sauce'],
                    'description': 'Cloudify generated FirewallRule',
                    'sourceRanges': ['1'],
                    'allowed': [{'IPProtocol': 'tcp', 'ports': 'pct'}],
                    'name': 'name'},
                project='not really a project'
                )

    def test_create_external(self, mock_build, *args):
        self.ctxmock.node.properties['use_external_resource'] = True

        firewall.create(
                'name',
                allowed={},
                sources={},
                target_tags=None,
                additional_settings={},
                )

        mock_build.assert_called_once()
        mock_build().firewalls().get.assert_called_once_with(
                firewall=True,
                project='not really a project'
                )

    def test_delete(self, mock_build, *args):
        self.ctxmock.instance.runtime_properties['name'] = 'delete_name'
        firewall.delete()

        mock_build.assert_called_once()
        mock_build().firewalls().delete.assert_called_with(
                firewall='delete-name',
                project='not really a project',
                )
