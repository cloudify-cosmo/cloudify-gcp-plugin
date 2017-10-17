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

from time import sleep
from urllib2 import urlopen, HTTPError

from cosmo_tester.framework.testenv import TestCase

from . import GCPTest


class GCPHttpForwardingTest(GCPTest, TestCase):
    blueprint_name = 'http_forwarding/global-static-ip-blueprint.yaml'

    inputs = {
            'gcp_auth',
            'project',
            }

    def assertions(self):

        for i in range(40):
            sleep(10)
            try:
                text = urlopen('http://{}/'.format(
                    self.outputs['ip_ip'])).read()

                self.assertEqual(
                        self.outputs['vm_name'],
                        text.strip())
            except (AssertionError, HTTPError) as e:
                print('attempt {}/40: {}'.format(i, e))
            else:
                break
        else:
            self.fail('tried too many times to get the page')
