# #######
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

from mock import patch, MagicMock

from cloudify.exceptions import NonRecoverableError

from .. import ssl_certificate
from ...tests import TestGCP


def _get_pem_data(type, data):
    return '{}: {}'.format(type, data)


@patch('cloudify_gcp.gcp.ServiceAccountCredentials.from_json_keyfile_dict')
@patch('cloudify_gcp.gcp.build')
class TestSslCertificate(TestGCP):

    @patch('cloudify_gcp.compute.ssl_certificate.get_pem_data',
           side_effect=_get_pem_data)
    @patch('cloudify_gcp.utils.response_to_operation')
    def test_create(self, mock_response, mock_get_pem, mock_build, *args):

        operation = MagicMock()
        operation.get.side_effect = [
                {'status': 'PENDING'},
                {'status': 'DONE'},
                ]

        operation.has_finished.return_value = True
        mock_response.return_value = operation

        ssl_certificate.create(
                'name',
                {'type': 'text', 'data': 'key data'},
                {'type': 'text', 'data': 'cert data'},
                )

        mock_build().sslCertificates().insert.assert_called_once_with(
                body={
                    'privateKey': 'text: key data',
                    'description': 'Cloudify generated SSL certificate',
                    'certificate': 'text: cert data',
                    'name': 'name',
                    },
                project='not really a project',
                )

        ssl_certificate.create(
                'name',
                {'type': 'file', 'data': 'key data'},
                {'type': 'file', 'data': 'cert data'},
                )

        mock_build().sslCertificates().insert.assert_called_with(
                body={
                    'privateKey': 'text: key data',
                    'description': 'Cloudify generated SSL certificate',
                    'certificate': 'text: cert data',
                    'name': 'name',
                    },
                project='not really a project',
                )

    def test_delete(self, mock_build, *args):
        self.ctxmock.instance.runtime_properties['name'] = 'delete me'

        ssl_certificate.delete()

        mock_build().sslCertificates().delete.assert_called_once_with(
                project='not really a project',
                sslCertificate='delete me',
                )

    def test_get_pem_data_text(self, *args):
        self.assertEqual('out', ssl_certificate.get_pem_data('text', 'out'))

    def test_get_pem_data_raises(self, *args):
        with self.assertRaises(NonRecoverableError) as e:
            ssl_certificate.get_pem_data('type', 'data')

        self.assertIn('Unknown type', e.exception.message)

    @patch('cloudify_gcp.compute.ssl_certificate.open')
    def test_get_pem_data_file(self, mock_open, *args):
        fh = mock_open.return_value.__enter__.return_value
        fh.read.return_value = 'file contents'

        data = ssl_certificate.get_pem_data('file', 'data')

        mock_open.assert_called_once_with(self.ctxmock.download_resource())

        self.assertEqual('file contents', data)

    @patch('cloudify_gcp.compute.ssl_certificate.open')
    def test_get_pem_data_file_raises(self, mock_open, *args):
        def raiser(*args):
            raise IOError()
        mock_open.side_effect = raiser

        with self.assertRaisesRegexp(NonRecoverableError, 'Error .*reading'):
            ssl_certificate.get_pem_data('file', 'non existent')
