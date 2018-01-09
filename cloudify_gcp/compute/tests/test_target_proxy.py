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

import unittest

from mock import patch, MagicMock

from cloudify.exceptions import NonRecoverableError

from cloudify_gcp.compute import target_proxy
from ...tests import TestGCP


@patch('cloudify_gcp.utils.assure_resource_id_correct', return_value=True)
@patch('cloudify_gcp.gcp.ServiceAccountCredentials.from_json_keyfile_dict')
@patch('cloudify_gcp.utils.get_gcp_resource_name', return_value='valid_name')
@patch('cloudify_gcp.gcp.build')
class TestTargetProxy(TestGCP):

    def test_create_http(self, mock_build, *args):
        self.ctxmock.node.properties.update({
            'url_map': u'🗺',
            })

        target_proxy.create(
                'name',
                'http',
                'url map',
                ssl_certificate=None,
                service=None,
                additional_settings={},
                )

        mock_build.assert_called_once()
        mock_build().targetHttpProxies().insert.assert_called_with(
                body={
                    'urlMap': 'url map',
                    'description': 'Cloudify generated TargetHttpProxy',
                    'name': 'name'},
                project='not really a project'
                )

    def test_create_https(self, mock_build, *args):
        self.ctxmock.node.properties.update({
            'url_map': u'🗺',
            })

        target_proxy.create(
                'name',
                'https',
                'url map',
                ssl_certificate='cert',
                service=None,
                additional_settings={},
                )

        mock_build.assert_called_once()
        mock_build().targetHttpsProxies().insert.assert_called_with(
                body={
                    'urlMap': 'url map',
                    'sslCertificates': ['cert'],
                    'description': 'Cloudify generated TargetHttpsProxy',
                    'name': 'name'},
                project='not really a project'
                )

    def test_create_tcp(self, mock_build, *args):
        self.ctxmock.node.properties.update({
            'service': 'link'
            })

        target_proxy.create(
                'name',
                'tcp',
                None,
                service='link',
                ssl_certificate=None,
                additional_settings={},
                )

        mock_build.assert_called_once()
        mock_build().targetTcpProxies().insert.assert_called_with(
                body={
                    'service': 'link',
                    'description': 'Cloudify generated TargetTcpProxy',
                    'name': 'name'},
                project='not really a project'
                )

    def test_create_ssl(self, mock_build, *args):
        self.ctxmock.node.properties.update({
            'service': 'link'
            })

        target_proxy.create(
                'name',
                'ssl',
                None,
                ssl_certificate='cert',
                service='link',
                additional_settings={},
                )

        mock_build.assert_called_once()
        mock_build().targetSslProxies().insert.assert_called_with(
                body={
                    'service': 'link',
                    'sslCertificates': ['cert'],
                    'description': 'Cloudify generated TargetSslProxy',
                    'name': 'name'},
                project='not really a project'
                )

    @patch('cloudify_gcp.utils.response_to_operation')
    def test_delete(self, mock_response, mock_build, *args):
        self.ctxmock.instance.runtime_properties.update({
            'name': 'delete_name',
            'kind': 'compute#targetHttpProxy',
            })

        operation = MagicMock()
        operation.has_finished.return_value = True
        mock_response.return_value = operation

        target_proxy.delete()

        mock_build.assert_called_once()
        mock_build().targetHttpProxies().delete.assert_called_with(
                targetHttpProxy='delete_name',
                project='not really a project',
                )


class TestTargetProxyHelpers(unittest.TestCase):

    def test_target_proxy_of_type_raises(self):
        with self.assertRaises(NonRecoverableError) as e:
            target_proxy.target_proxy_of_type('http', ssl_certificate=' ')

        self.assertIn('SSL', e.exception.message)

        with self.assertRaises(NonRecoverableError) as e:
            target_proxy.target_proxy_of_type('carrots', ssl_certificate=' ')

        self.assertIn('Unexpected type', e.exception.message)
