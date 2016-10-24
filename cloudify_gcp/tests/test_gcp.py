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

from __future__ import print_function

import unittest
from mock import MagicMock, patch

from googleapiclient.errors import HttpError

from cloudify_gcp.tests.test_utils import NS
from cloudify_gcp import gcp


class TestGCP(unittest.TestCase):

    def test_check_response_decorator(self):

        class TestClass(object):

            def __init__(self):
                self.logger = MagicMock()

            @gcp.check_response
            def test_function(self, response):
                return response

        TestClass().test_function({})

        instance = TestClass()
        with self.assertRaises(gcp.GCPError):
            instance.test_function({'error': 'yay!'})

        instance.logger.error.assert_called_once()

    @patch('cloudify_gcp.gcp.GoogleCloudPlatform.create_discovery')
    @patch('cloudify_gcp.gcp.build')
    def test_get_common_instance_metadata(self, mock_build, mock_discovery):
        instance = gcp.GoogleCloudPlatform(
                config=MagicMock(),
                logger=MagicMock(),
                name='fred')

        metadata = instance.get_common_instance_metadata()

        mock_discovery().projects().get().execute(
                ).__getitem__.assert_called_once_with('commonInstanceMetadata')

        self.assertEqual(
                mock_discovery().projects().get().execute().__getitem__(),
                metadata)

    def test_is_missing_resource_error(self):
        for exception, output in [
                (None, False),
                (HttpError(NS(status=404), ''), True),
                (HttpError(NS(status=401), ''), False),
                ]:
            print("Testing {}. Should be {}".format(exception, output))
            self.assertIs(
                    gcp.is_missing_resource_error(exception),
                    output)

    def test_is_resource_used_error(self):
        for exception, output in [
                (None, False),
                (HttpError(NS(status=400), ''), True),
                (HttpError(NS(status=404), ''), False),
                ]:
            print("Testing {}. Should be {}".format(exception, output))
            self.assertIs(
                    gcp.is_resource_used_error(exception),
                    output)
