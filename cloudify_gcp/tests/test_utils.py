# -*- coding: utf-8 -*-
########
# Copyright (c) 2014-2020 Cloudify Platform Ltd. All rights reserved
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

import unittest
import json
from functools import partial

from mock import Mock, patch, PropertyMock, MagicMock

from cloudify.state import current_ctx
from cloudify.mocks import MockCloudifyContext
from cloudify.manager import DirtyTrackingDict
from cloudify.exceptions import NonRecoverableError

from cloudify_gcp import utils
from . import TestGCP


class NS(object):
    """Simple namespace helper"""

    reason = 'No reason needed for these tests'

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


def raiser(code):
    raise utils.HttpError(NS(status=code), ''.encode('utf-8'))


class TestUtils(unittest.TestCase):
    def test_get_item_from_gcp_response(self):
        item = {'name': 'test'}
        sth_that_has_items = {'items': [item]}
        found_item = utils.get_item_from_gcp_response(
            'name',
            'test',
            sth_that_has_items)
        self.assertEqual(found_item, item)

        found_item = utils.get_item_from_gcp_response(
            'name',
            'test2',
            sth_that_has_items)
        self.assertIsNone(found_item)

    def test_get_resource_name(self):
        for input, output in [
                ('test_resource_name1', 'test-resource-name1'),  # underscores
                ('a' * 70, 'a' * 63),  # too long
                ('test_345%$*^&()+_sd^*()', 'test-345-sd'),  # invalid chars
                ('a' * 70 + '_123ab', 'a' * 57 + '-123ab'),  # also too long
                ('3', 'a3'),  # must start with alpha
                ("a-b-c---", "a-b-c"),  # dashes at the end
                ]:
            self.assertEqual(output, utils.get_gcp_resource_name(input))

    def test_camel_farm(self):
        for i, o in {
                'i': 'i',
                'hi_you': 'hiYou',
                'are_really_very': 'areReallyVery',
                'nice': 'nice',
                'proper_longer_example': 'properLongerExample',
                }.items():
            self.assertEqual(utils.camel_farm(i), o)

    def test_should_use_external_resource(self):
        fake_ctx = PropertyMock(return_value=MockCloudifyContext(properties={
            'use_external_resource': True,
        }))
        with patch('cloudify_gcp.utils.ctx', fake_ctx):
            self.assertTrue(utils.should_use_external_resource(fake_ctx))

    def test_throw_cloudify_exceptions(self):

        # create without error
        fake_ctx = MockCloudifyContext(
            'node_name',
            properties={},
        )
        fake_ctx._operation = Mock()
        fake_ctx.operation._operation_retry = None
        current_ctx.set(fake_ctx)
        fake_ctx.instance._runtime_properties = DirtyTrackingDict({"c": "d"})

        @utils.throw_cloudify_exceptions
        def test(*argc, **kwargs):
            return argc, kwargs

        fake_ctx._operation.name = "cloudify.interfaces.lifecycle.create"
        self.assertEqual(test(ctx=fake_ctx), ((), {'ctx': fake_ctx}))
        self.assertEqual(fake_ctx.instance._runtime_properties, {"c": "d"})

        # delete without error
        fake_ctx.instance._runtime_properties = DirtyTrackingDict({"a": "b"})
        fake_ctx._operation.name = "cloudify.interfaces.lifecycle.delete"
        self.assertEqual(test(ctx=fake_ctx), ((), {'ctx': fake_ctx}))
        self.assertFalse(fake_ctx.instance._runtime_properties)

        # delete postponed by gcp
        fake_ctx.instance._runtime_properties = DirtyTrackingDict(
            {"_operation": "b"})
        fake_ctx._operation.name = "cloudify.interfaces.lifecycle.delete"
        self.assertEqual(test(ctx=fake_ctx), ((), {'ctx': fake_ctx}))
        self.assertEqual(fake_ctx.instance._runtime_properties,
                         {"_operation": "b"})

        # postponed by cloudify
        @utils.throw_cloudify_exceptions
        def test(ctx, *argc, **kwargs):
            ctx.operation._operation_retry = 'Should be retried'
            return argc, kwargs

        fake_ctx.instance._runtime_properties = DirtyTrackingDict({"a": "b"})
        fake_ctx._operation.name = "cloudify.interfaces.lifecycle.delete"
        self.assertEqual(test(ctx=fake_ctx), ((), {}))
        self.assertEqual(fake_ctx.instance._runtime_properties, {"a": "b"})

        # postponed by exeption
        @utils.throw_cloudify_exceptions
        def test(ctx, *argc, **kwargs):
            raise Exception('Should be retried')

        fake_ctx.instance._runtime_properties = DirtyTrackingDict({"a": "b"})
        fake_ctx._operation.name = "cloudify.interfaces.lifecycle.delete"
        with self.assertRaises(NonRecoverableError):
            test(ctx=fake_ctx)

        self.assertEqual(fake_ctx.instance._runtime_properties, {"a": "b"})

    def test_is_object_deleted(self):
        obj = Mock()

        # Non-exception means the object was collected succesfully
        self.assertFalse(utils.is_object_deleted(obj))

        obj.get.side_effect = partial(raiser, 404)

        self.assertTrue(utils.is_object_deleted(obj))


@patch('cloudify_gcp.gcp.service_account.Credentials.'
       'from_service_account_info')
class TestUtilsWithCTX(TestGCP):

    @patch('cloudify_gcp.utils.assure_resource_id_correct')
    def test_get_final_resource_name(self, mock_assure_correct, *args):
        self.ctxmock.node.properties['use_external_resource'] = True

        out = utils.get_final_resource_name('name')

        self.assertIs('name', out)

    def test_assure_resource_id_correct(self, *args):
        self.ctxmock.node.properties['resource_id'] = 'valid'

        utils.assure_resource_id_correct()

    def test_assure_resource_id_correct_raises_no_id(self, *args):
        with self.assertRaises(NonRecoverableError) as e:
            utils.assure_resource_id_correct()

        self.assertIn('missing', str(e.exception))

    def test_assure_resource_id_correct_raises_invalid(self, *args):
        self.ctxmock.node.properties['resource_id'] = '!nv4l!|>'

        with self.assertRaises(NonRecoverableError) as e:
            utils.assure_resource_id_correct()

        self.assertIn('cannot be used', str(e.exception))

    def test_create_resource_external(self, *args):
        self.ctxmock.node.properties['use_external_resource'] = True

        resource = Mock()
        resource.get.side_effect = partial(raiser, 404)

        with self.assertRaises(NonRecoverableError):
            utils.create(resource)

        self.ctxmock.node.properties['name'] = 'some-name'
        resource.get.side_effect = partial(raiser, 403)

        with self.assertRaises(utils.HttpError):
            utils.create(resource)

    def test_create_resource_external_with_name(self, *args):
        self.ctxmock.node.properties['use_external_resource'] = True
        self.ctxmock.node.properties['name'] = 'name-in-properties'

        resource = MagicMock()
        utils.create(resource)
        self.assertEqual(
            self.ctxmock.instance.runtime_properties['resource_id'],
            'name-in-properties')

    def test_create_delete_resource_external(self, *args):
        self.ctxmock.node.properties['use_external_resource'] = True
        self.ctxmock.node.properties['name'] = 'name-in-properties'

        resource = MagicMock()
        utils.create(resource)
        utils.delete_if_not_external(resource)
        self.assertIsNone(self.ctxmock.instance.runtime_properties.get(
            'resource_id'))

    def test_create_resource_external_unequal_name_and_res_id(self, *args):
        self.ctxmock.node.properties['use_external_resource'] = True
        self.ctxmock.node.properties['name'] = 'name1'
        self.ctxmock.node.properties['resource_id'] = 'name2'

        resource = MagicMock()
        with self.assertRaises(NonRecoverableError):
            utils.create(resource)

    def test_create_resource_external_with_runtime_resource_id(self, *args):
        self.ctxmock.node.properties['use_external_resource'] = True
        self.ctxmock.instance.runtime_properties = {
            'resource_id': 'resource_id_in_runtime_props'
        }
        self.ctxmock.node.properties['name'] = 'name-in-properties'

        resource = MagicMock()
        utils.create(resource)
        self.assertEqual(
            self.ctxmock.instance.runtime_properties['resource_id'],
            'resource_id_in_runtime_props')

    def test_retry_on_failure_raises(self, *args):

        @utils.retry_on_failure('a message')
        def raise_http(code):
            raiser(code)

        raise_http(400)

        self.ctxmock.operation.retry.assert_called_once_with('a message', 30)

        with self.assertRaises(utils.HttpError):
            raise_http(404)

    @patch('cloudify_gcp.utils.check_output')
    def test_get_agent_ssh_key_string(self, mock_check_output, *args):
        mock_check_output.return_value = 'public 🗝'
        self.ctxmock.provider_context = {
            'cloudify': {
                'cloudify_agent': {
                    'agent_key_path': '🗝',
                    'user': '🙎',
                    }}}

        self.assertEqual(
                '🙎:public 🗝 🙎@cloudify',
                utils.get_agent_ssh_key_string())

    def test_get_agent_ssh_key_string_raises(self, *args):
        self.ctxmock.provider_context = {
            'cloudify': {
                'cloudify_agent': {
                    'agent_key_path': None,
                    'user': '🙎',
                    }}}

        with self.assertRaises(NonRecoverableError) as e:
            utils.get_agent_ssh_key_string()

        self.assertIn('key generation failure', str(e.exception))

    def test_get_gcp_config(self, *args):
        self.ctxmock.node.properties['gcp_config'] = {
                'zone': '3',
                'project': 'plan 9',
                'auth': {},
                }

        conf = utils.get_gcp_config()

        self.assertEqual('default', conf['network'])

    def test_get_gcp_config_json_input(self, *args):
        self.ctxmock.node.properties['gcp_config'] = json.loads(json.dumps({
            'zone': '3',
            'auth': '''{"type": "sa",
                    "project_id": "1",
                    "private_key_id": "2",
                    "private_key": "abcd",
                    "client_email": "svc@some_email",
                    "client_id": "3",
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "auth_provider_x509_cert_url":
                    "https://www.googleapis.com/oauth2/v1/certs",
                    "client_x509_cert_url": "https://www.googleapis.com/.."}'''
        }))

        auth_expected = json.loads(
            self.ctxmock.node.properties['gcp_config']['auth'])
        gcp_config_expected = {'zone': 3,
                               'project': '1',
                               'auth': auth_expected
                               }

        conf = utils.get_gcp_config()
        self.assertDictEqual(conf['auth'], gcp_config_expected['auth'])
        self.assertEqual(conf['project'], gcp_config_expected['project'])
        # pop 3 credential in the 'auth' json string

    def test_get_gcp_config_json_input_field_missing(self, *args):
        # auth_provider_x509_cert_url is missing
        self.ctxmock.node.properties['gcp_config'] = json.loads(json.dumps({
            'zone': '3',
            'auth': '''{"type": "sa",
                            "project_id": "1",
                            "private_key_id": "2",
                            "private_key": "abcd",
                            "client_email": "svc@some_email",
                            "client_id": "3",
                            "auth_uri":
                            "https://accounts.google.com/o/oauth2/auth",
                            "token_uri":"https://oauth2.googleapis.com/token",
                            "client_x509_cert_url":
                            "https://www.googleapis.com/..."}'''
        }))

        with self.assertRaises(NonRecoverableError):
            utils.get_gcp_config()

    def test_get_net_and_subnet(self, *args):
        self.assertEqual(
            ('projects/not really a project/'
             'global/networks/not a real network',
             None),
            utils.get_net_and_subnet(self.ctxmock.instance.relationships)
        )

    @patch('cloudify_gcp.utils.get_net_and_subnet')
    def test_get_network(self, mock_nands, *args):
        self.assertEqual(
                mock_nands.return_value.__getitem__.return_value,
                utils.get_network('hi'),
                )

    @patch('cloudify_gcp.utils.response_to_operation')
    def test_async_operation_failing_operation(self, mock_r2o, *args):
        self.ctxmock.instance.runtime_properties['_operation'] = 'rhinoplasty'
        mock_r2o.return_value.has_finished.side_effect = utils.GCPError('nooo')
        mock_r2o.return_value.last_response = {
            'status': 'DONE',
            'error': 'YEP! IT FAILED.',
        }

        class FakeNodeType(object):
            @utils.async_operation()
            def star_jump(self):
                return {
                        'a': 'response',
                        }

        fake_obj = FakeNodeType()

        with self.assertRaises(utils.GCPError) as e:
            fake_obj.star_jump()

        self.assertIs(
                e.exception,
                mock_r2o.return_value.has_finished.side_effect)
        self.assertNotIn(
                '_operation',
                self.ctxmock.instance.runtime_properties)
