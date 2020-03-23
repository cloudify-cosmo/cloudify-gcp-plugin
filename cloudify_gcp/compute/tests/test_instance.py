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

from functools import partial

from mock import patch, Mock

from cloudify.exceptions import NonRecoverableError

from .. import instance
from ...tests import TestGCP


utils_get_ssh_keys_patch = partial(
        patch,
        'cloudify_gcp.utils.get_agent_ssh_key_string',
        )


@patch('cloudify_gcp.gcp.ServiceAccountCredentials.from_json_keyfile_dict')
@patch('cloudify_gcp.utils.Operation.has_finished', return_value=True)
@patch('cloudify_gcp.gcp.build')
class TestGCPInstance(TestGCP):

    def setUp(self):
        super(TestGCPInstance, self).setUp()
        # Default from types.yaml.
        self.ctxmock.node.properties['os_family'] = 'linux'
        self.ctxmock.instance.runtime_properties['zone'] = 'a very fake zone'
        self.ctxmock.source.instance.runtime_properties = {
                'zone': 'a very fake zone',
                }
        self.ctxmock.node.properties.update({
                'install_agent': False,
                })
        self.ctxmock.agent.init_script = lambda: None \
            if self.ctxmock.node.properties['install_agent'] is False \
            else "SCRIPT STRING"

    def test__get_script_file(self, *args):
        instance._get_script({
            'type': 'file',
            'script': '/dev/null',
            })

        self.ctxmock.get_resource.assert_called_once_with('/dev/null')

    def test__get_script_string(self, *_):
        response = instance._get_script({
            'type': 'string',
            'script': '📜',
            })
        new_script_format = {
            'key': 'startup-script',
            'value': '📜'
        }
        self.assertEqual(new_script_format, response)

    def test__get_script_bare_string_old_format_input(self, *_):
        new_script_format = {
            'key': 'startup-script',
            'value': '🐻'
        }
        self.assertEqual(new_script_format, instance._get_script('🐻'))

    def test__get_script_bare_string_new_format_input(self, *_):
        new_script_format = {
            'key': 'startup-script',
            'value': '🐻'
        }
        self.assertEqual(new_script_format,
                         instance._get_script({
                                'key': 'startup-script',
                                'value': '🐻'}))

    def test_create(self, mock_build, *args):
        self.ctxmock.instance.runtime_properties.update({
                'startup_script': {'type': 'string'},
                })
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
                        'network': 'projects/not really a project/'
                                   'global/networks/not a real network',
                        }],
                    'canIpForward': False,
                    },
                project='not really a project',
                zone='zone'
                )

        self.assertEqual(
                {
                    'zone': 'zone',
                    'startup_script': {'type': 'string'},
                    'name': 'name',
                    'resource_id': 'name',
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
                    'resource_id': 'name',
                    },
                self.ctxmock.instance.runtime_properties
                )

    def test_create_with_disk(self, mock_build, *args):
        self.ctxmock.instance.runtime_properties.update({
                'gcp_disk': '💾',
                })
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
                        'network': 'projects/not really a project/'
                                   'global/networks/not a real network',
                        }],
                    'canIpForward': False,
                    },
                project='not really a project',
                zone='zone'
                )

    def test_create_2_boot_disks_raises(self, *args):
        self.ctxmock.instance.relationships = []
        for i in 1, 2:
            rel = Mock()
            rel.target.instance.runtime_properties = {
                    'kind': 'compute#disk',
                    'gcp_disk': {
                        'source': 'disk_{}'.format(i),
                        'boot': True,
                        },
                    }
            self.ctxmock.instance.relationships.append(rel)

        with self.assertRaises(NonRecoverableError) as e:
            instance.create(
                'type',
                'image',
                'name',
                external_ip=True,
                startup_script=None,
                scopes='scopes',
                tags=['tags'],
                )
        for name in 'disk_1', 'disk_2':
            self.assertIn(name, str(e.exception))

    def test_create_with_metadata(self, mock_build, *args):
        metadata = {'metadata': {'items': [{'key': 'k', 'value': 'v'}]}}
        instance.create(
            'type',
            'image',
            'name',
            external_ip=True,
            startup_script=None,
            scopes='scopes',
            tags=['tags'],
            additional_settings=metadata
        )

        mock_build().instances().insert.call_args[1][
            'body']['tags']['items'].sort()
        mock_build().instances().insert.assert_called_with(
            body={
                'machineType': 'zones/a very fake zone/machineTypes/type',
                'tags': {'items': ['name', 'tags']},
                'canIpForward': False,
                'metadata': {'items': [
                    {'key': 'k',
                     'value': 'v'},
                    {'value': 'not really a project',
                     'key': 'bucket'},
                    {'value': '',
                     'key': 'sshKeys'}
                ]},
                'networkInterfaces': [{
                    'network': 'projects/not really a project/'
                               'global/networks/not a real network',
                    'accessConfigs': [{
                        'type': 'ONE_TO_ONE_NAT',
                        'name': 'External NAT'}]
                }],
                'serviceAccounts': [{
                    'email': 'default',
                    'scopes': 'scopes'}],
                'name': 'name',
                'description': 'Cloudify generated instance',
                'disks': [{
                    'autoDelete': True,
                    'boot': True,
                    'initializeParams': {'sourceImage': 'image'}}]
            },
            project='not really a project',
            zone='a very fake zone',
        )

    def test_create_with_external_ip(self, mock_build, *args):
        instance.create(
                'type',
                'image',
                'name',
                external_ip=True,
                startup_script=None,
                scopes='scopes',
                tags=['tags'],
                )

        mock_build().instances().insert.call_args[1][
                'body']['tags']['items'].sort()
        mock_build().instances().insert.assert_called_with(
                body={
                    'machineType': 'zones/a very fake zone/machineTypes/type',
                    'tags': {'items': ['name', 'tags']},
                    'canIpForward': False,
                    'metadata': {'items': [
                        {'value': 'not really a project',
                         'key': 'bucket'},
                        {'value': '',
                            'key': 'sshKeys'}
                        ]},
                    'networkInterfaces': [{
                        'network': 'projects/not really a project/'
                                   'global/networks/not a real network',
                        'accessConfigs': [{
                            'type': 'ONE_TO_ONE_NAT',
                            'name': 'External NAT'}]
                        }],
                    'serviceAccounts': [{
                        'email': 'default',
                        'scopes': 'scopes'}],
                    'name': 'name',
                    'description': 'Cloudify generated instance',
                    'disks': [{
                        'autoDelete': True,
                        'boot': True,
                        'initializeParams': {'sourceImage': 'image'}}]
                    },
                project='not really a project',
                zone='a very fake zone',
                )

    @patch('cloudify_gcp.utils.get_network_node')
    @patch('cloudify_gcp.utils.get_net_and_subnet')
    def test_create_with_subnet(self, mock_g_ns, mock_g_nn, mock_build, *args):
        mock_g_ns.return_value = 'net', 'subnet'

        instance.create(
                'type',
                'image',
                'name',
                external_ip=True,
                startup_script=None,
                scopes='scopes',
                tags=['tags'],
                )

        mock_build().instances().insert.call_args[1][
                'body']['tags']['items'].sort()
        mock_build().instances().insert.assert_called_with(
                body={
                    'tags': {'items': ['name', 'tags']},
                    'machineType': 'zones/a very fake zone/machineTypes/type',
                    'name': 'name',
                    'canIpForward': False,
                    'disks': [{
                        'initializeParams': {'sourceImage': 'image'},
                        'boot': True,
                        'autoDelete': True}],
                    'networkInterfaces': [{
                        'accessConfigs': [{
                            'name': 'External NAT',
                            'type': 'ONE_TO_ONE_NAT'}],
                        'subnetwork': 'subnet',
                        'network': 'net'}],
                    'serviceAccounts': [{
                        'scopes': 'scopes',
                        'email': 'default'}],
                    'metadata': {'items': [
                        {'key': 'bucket', 'value': 'not really a project'},
                        {'key': 'sshKeys', 'value': ''}]},
                    'description': 'Cloudify generated instance'},
                project='not really a project',
                zone='a very fake zone',
                )

    def test_create_with_script(self, mock_build, *args):
        instance.create(
                'instance_type',
                'image_id',
                'name',
                zone='zone',
                external_ip=False,
                startup_script={
                    'type': 'string',
                    'script': 'Cyrillic',
                    },
                scopes='scopes',
                tags=['tags'],
                )

        mock_build().instances().insert.call_args[1][
                'body']['tags']['items'].sort()
        mock_build().instances().insert.assert_called_with(
                body={
                    'metadata': {
                        'items': [
                            {'key': 'bucket', 'value': 'not really a project'},
                            {'key': 'sshKeys', 'value': ''},
                            {'key': 'startup-script', 'value': 'Cyrillic'},
                            ]},
                        'tags': {'items': ['name', 'tags']},
                        'disks': [{
                            'boot': True,
                            'initializeParams': {'sourceImage': 'image_id'},
                            'autoDelete': True}],
                        'machineType': 'zones/zone/machineTypes/instance_type',
                        'serviceAccounts': [{
                            'email': 'default', 'scopes': 'scopes'}],
                        'name': 'name',
                        'canIpForward': False,
                        'description': 'Cloudify generated instance',
                        'networkInterfaces': [{
                            'network': 'projects/not really a project/global'
                                       '/networks/not a real network'}]
                        },
                project='not really a project', zone='zone'
                )

    def test_create_with_script_and_agent(self, mock_build, *args):
        self.ctxmock.node.properties['install_agent'] = True
        instance.create(
                'instance_type',
                'image_id',
                'name',
                zone='zone',
                external_ip=False,
                startup_script={
                    'type': 'string',
                    'script': 'Cyrillic',
                    },
                scopes='scopes',
                tags=['tags'],
                )

        mock_build().instances().insert.call_args[1][
                'body']['tags']['items'].sort()
        mock_build().instances().insert.assert_called_with(
                body={
                    'metadata': {
                        'items': [
                            {'key': 'bucket', 'value': 'not really a project'},
                            {'key': 'sshKeys', 'value': ''},
                            {'key': 'startup-script',
                             'value': 'Cyrillic\nSCRIPT STRING'},
                            ]},
                        'tags': {'items': ['name', 'tags']},
                        'disks': [{
                            'boot': True,
                            'initializeParams': {'sourceImage': 'image_id'},
                            'autoDelete': True}],
                        'machineType': 'zones/zone/machineTypes/instance_type',
                        'serviceAccounts': [{
                            'email': 'default', 'scopes': 'scopes'}],
                        'name': 'name',
                        'canIpForward': False,
                        'description': 'Cloudify generated instance',
                        'networkInterfaces': [{
                            'network': 'projects/not really a project/global'
                                       '/networks/not a real network'}]
                        },
                project='not really a project', zone='zone'
                )

    def test_create_with_script_and_windows_agent(self, mock_build, *args):
        self.ctxmock.node.properties['os_family'] = 'windows'
        self.ctxmock.node.properties['install_agent'] = True
        ps1 = '<powershell>SCRIPT STRING1\nSCRIPT_STRING2</powershell>'
        self.ctxmock.agent.init_script = Mock(return_value=ps1)
        instance.create(
                'instance_type',
                'image_id',
                'name',
                zone='zone',
                external_ip=False,
                startup_script={
                    'key': 'sysprep-specialize-script-ps1',
                    'value': 'Cyrillic',
                    },
                scopes='scopes',
                tags=['tags'],
                )

        mock_build().instances().insert.call_args[1][
                'body']['tags']['items'].sort()
        mock_build().instances().insert.assert_called_with(
                body={
                    'metadata': {
                        'items': [
                            {'key': 'bucket', 'value': 'not really a project'},
                            {'key': 'sshKeys', 'value': ''},
                            {'key': 'sysprep-specialize-script-ps1',
                             'value': '<powershell>\nCyrillic\n'
                                      '\nSCRIPT STRING1\n'
                                      'SCRIPT_STRING2\n\n'
                                      '</powershell>'},
                            ]},
                        'tags': {'items': ['name', 'tags']},
                        'disks': [{
                            'boot': True,
                            'initializeParams': {'sourceImage': 'image_id'},
                            'autoDelete': True}],
                        'machineType': 'zones/zone/machineTypes/instance_type',
                        'serviceAccounts': [{
                            'email': 'default', 'scopes': 'scopes'}],
                        'name': 'name',
                        'canIpForward': False,
                        'description': 'Cloudify generated instance',
                        'networkInterfaces': [{
                            'network': 'projects/not really a project/global'
                                       '/networks/not a real network'}]
                        },
                project='not really a project', zone='zone'
                )

    @patch('cloudify_gcp.utils.get_item_from_gcp_response',
           return_value={'networkInterfaces': [{'networkIP': 'a'}]})
    def test_start(self, mock_getitem, mock_build, *args):
        self.ctxmock.node.properties['external_ip'] = False
        self.ctxmock.instance.runtime_properties['name'] = 'name'
        instance.start()

        self.assertEqual(
                self.ctxmock.instance.runtime_properties['ip'],
                'a')

    @patch('cloudify_gcp.utils.get_item_from_gcp_response', return_value={
        'networkInterfaces': [
            {
                'networkIP': 'a',
                'accessConfigs': [{'natIP': '🕷'}],
            },
        ]})
    def test_start_with_external_ip(self, mock_getitem, mock_build, *args):
        self.ctxmock.node.properties['external_ip'] = True
        self.ctxmock.instance.runtime_properties['name'] = 'name'
        instance.start()

        self.assertEqual(
                self.ctxmock.instance.runtime_properties[
                    'networkInterfaces'][0]['accessConfigs'][0]['natIP'],
                '🕷')
        public_ip_address = self.ctxmock.instance.runtime_properties[
            'public_ip_address']
        self.assertEqual(public_ip_address, '🕷')

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
        self.ctxmock.instance.runtime_properties.update({
                'gcp_disk': 'hi',
                'name': 'delete-name',
                'zone': 'hey',
                'another': 'yo',
                '_operation': _op,
                })
        mock_build().globalOperations().get().execute.return_value = _op

        self.ctxmock.operation.name = "cloudify.interfaces.lifecycle.delete"
        self.ctxmock.operation._operation_retry = None

        instance.delete('delete-name', 'zone')

        self.assertFalse(mock_build().instances().delete.called)

        self.assertFalse(self.ctxmock.instance.runtime_properties)

    @patch('cloudify_gcp.utils.get_item_from_gcp_response', return_value={
                'networkInterfaces': [{'accessConfigs': [{'natIP': '🕷'}]}]})
    def test_add_external_ip(self, mock_getitem, mock_build, *args):
        self.ctxmock.target.node.type = 'cloudify.gcp.nodes.Address'
        self.ctxmock.target.node.properties = {
                'use_external_resource': False,
                }
        self.ctxmock.target.instance.runtime_properties = {
                'address': '100.acre.wood',
                }

        instance.add_external_ip('instance_name', 'a very fake zone')

        mock_build().instances().addAccessConfig.assert_called_once_with(
                body={
                    'kind': 'compute#accessConfig',
                    'name': 'External NAT',
                    'type': 'ONE_TO_ONE_NAT',
                    'natIP': '100.acre.wood'},
                instance='instance-name',
                networkInterface='nic0',
                project='not really a project',
                zone='a very fake zone',
                )

    @patch('cloudify_gcp.utils.get_item_from_gcp_response', return_value={
                'networkInterfaces': [{'accessConfigs': [{'natIP': '🕷'}]}]})
    def test_add_external_external_ip(self, mock_getitem, mock_build, *args):
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

    def test_add_external_external_ip_wrongtype(self, mock_build, *args):
        self.ctxmock.target.node.type = 'nope'
        self.ctxmock.target.node.properties = {
                'use_external_resource': False,
                }
        self.ctxmock.source.instance.runtime_properties = {
                'zone': 'zone',
                }
        self.ctxmock.target.instance.runtime_properties = {}

        with self.assertRaises(NonRecoverableError) as e:
            instance.add_external_ip('instance_name', 'zone')
        self.assertIn('Incorrect node type', str(e.exception))

    def test_create_external_resource(self, mock_build, *args):
        self.ctxmock.node.properties[
                'use_external_resource'] = True
        self.ctxmock.node.properties[
            'name'] = 'name'
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

    @utils_get_ssh_keys_patch(return_value='🗝')
    def test_get_ssh_key(self, mock_get_key_string, *args):
        self.ctxmock.node.properties['agent_config'] = {
                'install_method': 'remote',
                }
        self.ctxmock.node.properties.update({
                'install_agent': '',
                })

        keys = instance.get_ssh_keys()

        self.assertEqual(['🗝'], keys)

    @utils_get_ssh_keys_patch(return_value='🗝')
    def test_get_ssh_key_none(self, mock_get_key_string, *args):
        self.ctxmock.node.properties['agent_config'] = {
                'install_method': 'none',
                }

        keys = instance.get_ssh_keys()

        self.assertEqual([], keys)

    @utils_get_ssh_keys_patch(return_value='🗝')
    def test_get_ssh_key_none_legacy(self, mock_get_key_string, *args):
        self.ctxmock.node.properties['install_agent'] = False

        keys = instance.get_ssh_keys()

        self.assertEqual([], keys)
