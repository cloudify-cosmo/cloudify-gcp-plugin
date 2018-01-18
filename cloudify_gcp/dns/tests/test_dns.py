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

from mock import patch

from .. import dns
from ...tests import TestGCP


@patch('cloudify_gcp.gcp.ServiceAccountCredentials.from_json_keyfile_dict')
@patch('cloudify_gcp.utils.get_gcp_resource_name', return_value='valid_name')
@patch('cloudify_gcp.gcp.build')
class TestGCPDNS(TestGCP):

    def test_create(self, mock_build, *args):
        dns.create(
                'image', 'name',
                additional_settings={},
                )

        mock_build().managedZones().create.assert_called_once_with(
                body={
                    'dnsName': 'name',
                    'description': 'Cloudify generated DNS Zone',
                    'name': 'image'},
                project='not really a project'
                )

    def test_delete(self, mock_build, *args):
        self.ctxmock.instance.runtime_properties['name'] = 'delete_name'

        dns.delete()

        mock_build().managedZones().delete.assert_called_with(
                managedZone='delete_name',
                project='not really a project',
                )

    def test_delete_deleted(self, mock_build, *args):
        dns.delete()

        mock_build.assert_not_called()
