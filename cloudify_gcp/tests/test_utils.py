# -*- coding: utf-8 -*-
########
# Copyright (c) 2014 GigaSpaces Technologies Ltd. All rights reserved
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

import unittest
from functools import partial

from mock import Mock, patch, PropertyMock

from cloudify.exceptions import NonRecoverableError
from cloudify.mocks import MockCloudifyContext
from cloudify.state import current_ctx

from cloudify_gcp import utils


class NS(object):
    """Simple namespace helper"""

    reason = 'No reason needed for these tests'

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


def raiser(code):
    raise utils.HttpError(NS(status=code), '')


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
        with patch(
                'cloudify_gcp.utils.ctx',
                PropertyMock(
                    return_value=MockCloudifyContext(
                        properties={
                            'use_external_resource': True,
                        }))):
            self.assertTrue(utils.should_use_external_resource())

    def test_is_object_deleted(self):
        obj = Mock()

        # Non-exception means the object was collected succesfully
        self.assertFalse(utils.is_object_deleted(obj))

        obj.get.side_effect = partial(raiser, 404)

        self.assertTrue(utils.is_object_deleted(obj))


@patch('cloudify_gcp.gcp.ServiceAccountCredentials.from_json_keyfile_dict')
class TestUtilsWithCTX(unittest.TestCase):

    def setUp(self):
        ctx = self.ctxmock = Mock()
        ctx.node.properties = {}

        current_ctx.set(ctx)

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

        self.assertIn('missing', e.exception.message)

    def test_assure_resource_id_correct_raises_invalid(self, *args):
        self.ctxmock.node.properties['resource_id'] = '!nv4l!|>'

        with self.assertRaises(NonRecoverableError) as e:
            utils.assure_resource_id_correct()

        self.assertIn('cannot be used', e.exception.message)

    def test_create_resource_external(self, *args):
        self.ctxmock.node.properties['use_external_resource'] = True

        resource = Mock()
        resource.get.side_effect = partial(raiser, 404)

        with self.assertRaises(NonRecoverableError):
            utils.create(resource)

        resource.get.side_effect = partial(raiser, 403)

        with self.assertRaises(utils.HttpError):
            utils.create(resource)

    def test_retry_on_failure_raises(self, *args):

        @utils.retry_on_failure('a message')
        def raise_http(code):
            raiser(code)

        raise_http(400)

        self.ctxmock.operation.retry.assert_called_once_with('a message', 30)

        with self.assertRaises(utils.HttpError):
            raise_http(404)

    def test_get_agent_ssh_key_string(self, *args):
        self.ctxmock.provider_context = {}

        self.assertEqual('', utils.get_agent_ssh_key_string())

        self.ctxmock.provider_context['resources'] = {
                'cloudify_agent': {
                    'public_key': '🗝',
                    }}

        self.assertEqual('🗝', utils.get_agent_ssh_key_string())
