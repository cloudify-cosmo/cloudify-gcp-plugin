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

from cloudify.exceptions import NonRecoverableError

from .. import instance
from ...tests import TestGCP


@patch('cloudify_gcp.gcp.ServiceAccountCredentials.from_json_keyfile_dict')
@patch('cloudify_gcp.gcp.build')
class TestGCPInstance(TestGCP):

    def setUp(self):
        super(TestGCPInstance, self).setUp()
        self.ctxmock.instance.runtime_properties['zone'] = 'a very fake zone'
        self.ctxmock.source.instance.runtime_properties = {
                'zone': 'a very fake zone',
                }
        self.ctxmock.node.properties.update({
                'install_agent': False,
                })

    def test_create(self, mock_build, *args):
        self.ctxmock.instance.runtime_properties = {
                'startup_script': {'type': 'string'},
                }
        self.ctxmock.instance.relationships = []

        instance.create(
                'instance_type',
                'image_id',
                'name',
                zone='zone',
                external_ip=False,
                startup_script=None,
                scopes='scopes',
                tags=['tags'],
                )

        mock_build.assert_called_once()

        mock_build().instances().insert.call_args[1][
                'body']['tags']['items'].sort()
        mock_build().instances().insert.assert_called_with(
                body={
                    'machineType': 'zones/zone/machineTypes/instance_type',
                    'name': 'name',
                    'tags': {'items': ['name', 'tags']},
                    'description': 'Cloudify generated instance',
                    'disks': [{
                        'initializeParams': {'sourceImage': 'image_id'},
                        'boot': True, 'autoDelete': True}],
                    'serviceAccounts': [{
                        'scopes': 'scopes',
                        'email': 'default'}],
                    'metadata': {
                        'items': [
                            {'value': 'not really a project', 'key': 'bucket'},
                            {'value': '', 'key': 'sshKeys'}]},
                    'networkInterfaces': [{
                        'network': 'not a real network'}],
                    'canIpForward': False,
                    },
                project='not really a project',
                zone='zone'
                )

        self.assertEqual(
                {
                    'zone': 'zone',
                    'startup_script': {'type': 'string'},
                    '_operation': mock_build().instances().insert().execute(),
                 },
                self.ctxmock.instance.runtime_properties
                )

        # Simulate the operation being complete:
        mock_build().instances().get().execute.return_value = {
                'you pass': 'the test',
                }
        mock_build().globalOperations().get().execute.return_value = {
                'status': 'DONE',
                }

        # And the second time around create() should update runtime_properties
        instance.create(
                'instance_type',
                'image_id',
                'name',
                zone='zone',
                external_ip=False,
                startup_script=None,
                scopes='scopes',
                tags=['tags'],
                )

        self.assertEqual(
                {
                    'startup_script': {'type': 'string'},
                    'you pass': 'the test',
                    'zone': 'zone',
                    },
                self.ctxmock.instance.runtime_properties
                )

    def test_create_with_disk(self, mock_build, *args):
        self.ctxmock.instance.runtime_properties = {
                'gcp_disk': '💾',
                }
        self.ctxmock.instance.relationships = []

        instance.create(
                'instance_type',
                'image_id',
                'name',
                zone='zone',
                external_ip=False,
                startup_script=None,
                scopes='scopes',
                tags=['tags'],
                )

        mock_build().instances().insert.call_args[1][
                'body']['tags']['items'].sort()
        mock_build().instances().insert.assert_called_with(
                body={
                    'machineType': 'zones/zone/machineTypes/instance_type',
                    'name': 'name',
                    'tags': {'items': ['name', 'tags']},
                    'description': 'Cloudify generated instance',
                    'disks': ['💾'],
                    'serviceAccounts': [{
                        'scopes': 'scopes',
                        'email': 'default'}],
                    'metadata': {
                        'items': [
                            {'value': 'not really a project', 'key': 'bucket'},
                            {'value': '', 'key': 'sshKeys'}]},
                    'networkInterfaces': [{
                        'network': 'not a real network'}],
                    'canIpForward': False,
                    },
                project='not really a project',
                zone='zone'
                )

    @patch('cloudify_gcp.utils.get_item_from_gcp_response',
           return_value={'networkInterfaces': [{'networkIP': 'a'}]})
    def test_start(self, mock_getitem, mock_build, *args):
        self.ctxmock.instance.runtime_properties['name'] = 'name'
        instance.start()

        self.assertEqual(
                self.ctxmock.instance.runtime_properties['ip'],
                'a')

    def test_delete(self, mock_build, *args):
        instance.delete('delete-name', 'a very fake zone')

        mock_build.assert_called_once()
        mock_build().instances().delete.assert_called_with(
                instance='delete-name',
                project='not really a project',
                zone='a very fake zone')

    @patch('cloudify_gcp.utils.is_object_deleted', return_value=True)
    def test_delete_deleted(self, mock_is_deleted, mock_build, *args):
        _op = {
                'status': 'DONE',
                'name': 'op_name',
                }
        self.ctxmock.instance.runtime_properties = {
                'gcp_disk': 'hi',
                'name': 'delete-name',
                'zone': 'hey',
                'another': 'yo',
                '_operation': _op,
                }
        mock_build().globalOperations().get().execute.return_value = _op

        instance.delete('delete-name', 'zone')

        self.assertFalse(mock_build().instances().delete.called)

        self.assertEqual(
                {'another': 'yo', 'zone': 'hey'},
                self.ctxmock.instance.runtime_properties)

    def test_add_external_ip(self, mock_build, *args):
        self.ctxmock.target.node.properties = {
                'use_external_resource': False,
                }

        instance.add_external_ip('instance_name', 'a very fake zone')

        mock_build().instances().addAccessConfig.assert_called_once_with(
                body={
                    'kind': 'compute#accessConfig',
                    'type': 'ONE_TO_ONE_NAT',
                    'name': 'External NAT'},
                instance='instance-name',
                networkInterface='nic0',
                project='not really a project',
                zone='a very fake zone')

    def test_add_external_external_ip(self, mock_build, *args):
        self.ctxmock.target.node.properties = {
                'use_external_resource': True,
                }
        self.ctxmock.target.instance.runtime_properties = {
                'gcp_ip': "1.2.3.4",
                }

        instance.add_external_ip('instance_name', 'zone')

        mock_build().instances().addAccessConfig.assert_called_once_with(
                body={
                    'natIP': '1.2.3.4',
                    'kind': 'compute#accessConfig',
                    'type': 'ONE_TO_ONE_NAT',
                    'name': 'External NAT'},
                instance='instance-name',
                networkInterface='nic0',
                project='not really a project',
                zone='zone')

    def test_add_external_external_ip_raises(self, mock_build, *args):
        self.ctxmock.target.node.properties = {
                'use_external_resource': True,
                }
        self.ctxmock.source.instance.runtime_properties = {
                'zone': 'zone',
                }
        self.ctxmock.target.instance.runtime_properties = {}

        with self.assertRaises(NonRecoverableError):
            instance.add_external_ip('instance_name', 'zone')

    def test_create_external_resource(self, mock_build, *args):
        self.ctxmock.node.properties[
                'use_external_resource'] = True
        get_resp = object()
        mock_build().instances().get().execute.return_value = {
                'name': 'yes',
                'hi': get_resp,
                }

        instance.create(
                'instance_type',
                'image_id',
                'name',
                zone='zone',
                external_ip=False,
                startup_script=None,
                scopes='scopes',
                tags=['tags'],
                )

        self.assertEqual(0, mock_build().instances().insert.call_count)
        self.assertEqual(
                get_resp,
                self.ctxmock.instance.runtime_properties['hi']
                )

    def test_remove_external_ip(self, mock_build, *args):

        instance.remove_external_ip('instance_name', 'a very fake zone')

        mock_build().instances().deleteAccessConfig.assert_called_once_with(
                accessConfig='External NAT',
                instance='instance-name',
                networkInterface='nic0',
                project='not really a project',
                zone='a very fake zone',
                )

    def test_attach_disk(self, mock_build, *args):
        instance.attach_disk('instance', 'zone', 'disk')

        mock_build().instances().attachDisk.assert_called_once_with(
                body='disk',
                instance='instance',
                project='not really a project',
                zone='zone'
                )

    def test_detach_disk(self, mock_build, *args):
        instance.detach_disk('instance', 'zone', 'disk')

        mock_build().instances().detachDisk.assert_called_once_with(
                deviceName='disk',
                instance='instance',
                project='not really a project',
                zone='zone',
                )

    def test_add_ssh_key(self, mock_build, *args):
        self.ctxmock.target.instance.runtime_properties = {
                'gcp_public_key': 'ssh-rsa blahblabhalblah',
                'user': 'test_user',
                }
        self.ctxmock.source.instance.runtime_properties = {}

        instance.add_ssh_key()

        self.assertEqual(
                self.ctxmock.source.instance.runtime_properties['ssh_keys'],
                ['test_user:ssh-rsa blahblabhalblah test_user'])

    def test_add_instance_tag(self, mock_build, *args):
        mock_build().instances().get().execute.return_value = {
                'tags': {
                    'items': ['a', 'b', 'c'],
                    'fingerprint': u'🖐'}}

        instance.add_instance_tag('instance', 'zone', ['a tag'])

        # Something weird happens so we can't be sure of the order of tags
        mock_build().instances().setTags.call_args[1]['body']['items'].sort()
        mock_build().instances().setTags.assert_called_once_with(
            body={
                'items': ['a', 'atag', 'b', 'c'],
                'fingerprint': u'🖐'},
            project='not really a project',
            instance='instance',
            zone='zone'
            )

    @patch('cloudify_gcp.utils.get_gcp_resource_name',
           return_value='valid_name')
    def test_remove_instance_tag(self, mock_get_res, mock_build, *args):
        self.ctxmock.source.instance.runtime_properties = {
                'zone': 'zone',
                }
        mock_build().instances().get().execute.return_value = {
                'tags': {
                    'items': ['a tag', 'another tag'],
                    'fingerprint': u'🖐'}}

        mock_get_res.side_effect = lambda x: x

        instance.remove_instance_tag('instance', 'zone', ['a tag'])

        mock_build().instances().setTags.assert_called_once_with(
            body={
                'items': ['another tag'],
                'fingerprint': u'🖐'},
            project='not really a project',
            instance='instance',
            zone='zone'
            )

    def test_contained_in(self, *args):
        self.ctxmock.source.instance.runtime_properties = {}
        self.ctxmock.target.instance.runtime_properties = {
                'ssh_keys': '🗝🔑🗝',
                }

        instance.contained_in()

        self.assertEqual(
                '🗝🔑🗝',
                self.ctxmock.source.instance.runtime_properties['ssh_keys'])
