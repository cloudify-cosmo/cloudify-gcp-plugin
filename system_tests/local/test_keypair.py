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

import subprocess
from time import sleep

from cosmo_tester.framework.testenv import TestCase

from . import GCPTest


class GCPSimpleKeyPairTest(GCPTest, TestCase):
    blueprint_name = 'keypair/simple-blueprint.yaml'

    inputs = {
            'gcp_auth',
            'project',
            }

    def assertions(self):

        for i in range(12):
            sleep(5)
            try:
                hostname = subprocess.check_output([
                    'ssh',
                    '-i', 'gcp_systest.key',
                    '-o', 'UserKnownHostsFile=/dev/null',
                    '-o', 'StrictHostKeyChecking=no',
                    'keypair-user@{}'.format(self.outputs['ip']),
                    'hostname',
                    ])
            except subprocess.CalledProcessError as e:
                print('attempt {}: {}'.format(i, e))
            else:
                break
        else:
            self.fail('failed to log in via SSH')

        self.assertEqual(
                self.outputs['name'],
                hostname.strip())
