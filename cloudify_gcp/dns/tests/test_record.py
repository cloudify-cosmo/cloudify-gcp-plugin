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

from mock import Mock, patch

from .. import record
from ...tests import TestGCP


@patch('cloudify_gcp.gcp.ServiceAccountCredentials.from_json_keyfile_dict')
@patch('cloudify_gcp.utils.get_gcp_resource_name', return_value='valid_name')
@patch('cloudify_gcp.gcp.build')
class TestGCPRecord(TestGCP):

    def setUp(self):
        super(TestGCPRecord, self).setUp()

        rel = Mock()
        rel.type = 'cloudify.gcp.relationships.dns_record_contained_in_zone'
        rel.target.instance.runtime_properties = {
                'name': 'target instance',
                'dnsName': 'example.com.',
                }
        self.ctxmock.instance.relationships = [rel]

    def test_create(self, mock_build, *args):
        mock_build().changes().create().execute.side_effect = [
                {'status': 'pending', 'id': u'🛂'},
                {'status': 'done'},
                ]

        mock_build().changes().get().execute.side_effect = [
                {'status': 'pending', 'id': u'🛂'},
                {'status': 'done'},
                ]

        record.create(
                'type',
                'name',
                'resources',
                'ttl',
                )

        mock_build().changes().create.assert_called_with(
                body={
                    'additions': [{
                        'rrdatas': 'resources',
                        'type': 'type',
                        'name': 'name.example.com.',
                        'ttl': 'ttl',
                        }]},
                managedZone='target instance',
                project='not really a project',
                )

    def test_create_with_instance(self, mock_build, *args):
        mock_build().changes().create().execute.side_effect = [
                {'status': 'done'},
                ]

        rel = Mock()
        rel.type = ('cloudify.gcp.relationships.'
                    'dns_record_connected_to_instance')
        rel.target.instance.runtime_properties = {
                'networkInterfaces': [{'accessConfigs': [{
                    'natIP': 'intellectual property',
                    }]}],
                }
        # rel_target is the Instance instance context. The instance itself must
        # be connected to an external IP, so we need to mock its relationships
        # too
        rel_rel = Mock()
        rel_rel.type = 'cloudify.gcp.relationships.instance_connected_to_ip'
        rel.target.instance.relationships = [rel_rel]
        self.ctxmock.instance.relationships.append(rel)

        record.create(
                'type',
                'name',
                [],
                'ttl',
                )

        mock_build().changes().create.assert_called_with(
                body={
                    'additions': [{
                        'rrdatas': ['intellectual property'],
                        'type': 'type',
                        'name': 'name.example.com.',
                        'ttl': 'ttl',
                        }]},
                managedZone='target instance',
                project='not really a project',
                )

    def test_delete(self, mock_build, *args):
        self.ctxmock.node.properties['type'] = 'A'
        self.ctxmock.instance.runtime_properties = {
                'created': True,
                'name': 'delete me',
                }

        mock_build().resourceRecordSets().list().execute.return_value = {
                'rrsets': ['rrs'],
                }
        mock_build().resourceRecordSets().list_next.return_value = None

        mock_build().changes().create().execute.side_effect = [
                {'status': 'pending', 'id': u'🛂'},
                {'status': 'done'},
                ]

        mock_build().changes().get().execute.side_effect = [
                {'status': 'pending', 'id': u'🛂'},
                {'status': 'done'},
                ]

        record.delete()

        mock_build().changes().create.assert_called_with(
                body={'deletions': ['rrs']},
                managedZone='target instance',
                project='not really a project',
                )

    def test_delete_deleted(self, mock_build, *args):
        record.delete()

        mock_build.assert_not_called()
