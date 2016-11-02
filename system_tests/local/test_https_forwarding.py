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

import ssl
from time import sleep
from httplib import HTTPSConnection

from OpenSSL import crypto

from cosmo_tester.framework.testenv import TestCase

from . import GCPTest


def create_cert_pair():
    key = crypto.PKey()
    key.generate_key(crypto.TYPE_RSA, 2048)

    cert = crypto.X509()

    subj = cert.get_subject()
    subj.C = 'US'
    subj.ST = 'Disbelief'
    subj.L = 'Nowhere'
    subj.O = 'Bad Company'
    subj.OU = 'R&D'
    subj.CN = 'fake.getcloudfiy.org'

    cert.gmtime_adj_notBefore(0)
    cert.gmtime_adj_notAfter(8640)

    cert.set_issuer(cert.get_subject())
    cert.set_pubkey(key)
    cert.sign(key, 'sha1')

    return (crypto.dump_certificate(crypto.FILETYPE_PEM, cert),
            crypto.dump_privatekey(crypto.FILETYPE_PEM, key))


class GCPHttpsForwardingTest(GCPTest, TestCase):
    blueprint_name = 'http_forwarding/global-https-static-ip-blueprint.yaml'

    inputs = {
            'gcp_auth',
            'project',
            }

    def pre_install_hook(self):
        # Put SSL key and cert in the inputs

        self.cert, key = create_cert_pair()
        self.ext_inputs['ssl_cert'] = self.cert
        self.ext_inputs['ssl_key'] = key

    def assertions(self):

        # Write the cert to disk
        with open('https-forwarder-test-cert', 'w') as f:
            f.write(self.ext_inputs['ssl_cert'])

        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
        ssl_context.verify_mode = ssl.CERT_REQUIRED
        ssl_context.load_verify_locations('https-forwarder-test-cert')

        for i in range(20):
            sleep(5)

            try:
                http = HTTPSConnection(
                        self.outputs['ip_ip'], context=ssl_context)

                # If the certificate isn't the one we provided
                # this step will fail...
                http.request('GET', '/')
            except ssl.SSLError as e:
                print('attempt {}: {}'.format(i, e))
            else:
                break
        else:
            self.fail('continual SSL errors')

        # TODO: check http response body, once the startup-script issue is
        # resolved.
        # https://code.google.com/p/google-compute-engine/issues/detail?id=433

        assert False
