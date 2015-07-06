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

from gcp.compute import utils


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
        resource_name = 'test_resource_name1'
        resource_name_correct = 'test-resource-name1'
        result = utils.get_gcp_resource_name(resource_name)
        self.assertEqual(result, resource_name_correct)

        resource_name_too_long = 'a' * 70
        resource_name_too_long_correct = 'a' * 63
        result = utils.get_gcp_resource_name(resource_name_too_long)
        self.assertEqual(result, resource_name_too_long_correct)

        resource_name_nonalpha = 'test_345%$*^&()+_sd^*()'
        resource_name_nonalpha_correct = 'test-345-sd'
        result = utils.get_gcp_resource_name(resource_name_nonalpha)
        self.assertEqual(result, resource_name_nonalpha_correct)

        resource_name_too_long2 = 'a' * 70 + '_123ab'
        resource_name_too_long2_correct = 'a' * 57 + '-123ab'
        result = utils.get_gcp_resource_name(resource_name_too_long2)
        self.assertEqual(result, resource_name_too_long2_correct)
