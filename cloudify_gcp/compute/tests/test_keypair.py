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

from .. import keypair
from ...tests import TestGCP


@patch('cloudify_gcp.utils.assure_resource_id_correct', return_value=True)
@patch('cloudify_gcp.utils.get_key_user_string', side_effect=lambda x: x)
@patch('cloudify_gcp.utils.get_gcp_resource_name', return_value='valid_name')
@patch('os.chmod')
@patch('cloudify_gcp.compute.keypair.open')
@patch('cloudify_gcp.compute.keypair.RSA.generate')
class TestGCPKeypair(TestGCP):

    def test_create(self, mock_rsa, *args):
        keypair.create(
                'user',
                'private',
                'public',
                )

        mock_rsa.assert_called_once_with(2048)

        self.assertEqual(
                {'gcp_private_key': mock_rsa().exportKey(),
                 'gcp_public_key': mock_rsa().exportKey(),
                 'user': 'user'},
                self.ctxmock.instance.runtime_properties)

    def test_create_external(self, *args):
        self.ctxmock.node.properties['use_external_resource'] = True

        keypair.create(
                'user',
                'private',
                'public'
                )

        self.assertEqual(2, self.ctxmock.get_resource.call_count)

        for call_arg in 'public', 'private':
            self.ctxmock.get_resource.assert_any_call(call_arg)

        self.assertEqual(
                {'gcp_private_key': self.ctxmock.get_resource(),
                 'gcp_public_key': self.ctxmock.get_resource(),
                 'user': 'user'},
                self.ctxmock.instance.runtime_properties)

    def test_create_no_user(self, *args):

        with self.assertRaises(NonRecoverableError) as e:
            keypair.create(
                    '',
                    'private',
                    'public',
                    )

        self.assertIn('empty user', e.exception.message)

    def test_delete(self, *args):
        self.ctxmock.instance.runtime_properties[
                'gcp_public_key'] = 'delete_pubkey'

        keypair.delete(
                'user',
                'private',
                )

        self.assertEqual(
                {},
                self.ctxmock.instance.runtime_properties)
