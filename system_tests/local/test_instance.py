########
# Copyright (c) 2015 GigaSpaces Technologies Ltd. All rights reserved
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

from cosmo_tester.framework.testenv import TestCase

from . import GCPTest


class GCPInstanceTest(GCPTest, TestCase):
    blueprint_name = 'compute/simple-blueprint.yaml'

    inputs = (
            'project',
            'network',
            'zone',
            'gcp_auth',
            'image_id',
            )

    def assertions(self):
        self.assertEqual(
                self.outputs['name'],
                self.test_env.storage.get_node_instances('vm')[0][
                    'runtime_properties']['name']
                )


class GCPEphemeralIPTest(GCPTest, TestCase):
    blueprint_name = 'compute/external-ip-blueprint.yaml'

    inputs = (
            'project',
            'network',
            'zone',
            'gcp_auth',
            'image_id',
            )

    def assertions(self):
        vm = self.test_env.storage.get_node_instances('vm')[0]

        ephemeral_ip = vm['runtime_properties']['networkInterfaces'][0][
                'accessConfigs'][0]['natIP']

        self.assertIP(ephemeral_ip)


class GCPExternalIPPropertyTest(GCPTest, TestCase):
    blueprint_name = 'compute/external-ip-property-blueprint.yaml'

    inputs = (
            'project',
            'network',
            'zone',
            'gcp_auth',
            'image_id',
            )

    def assertions(self):
        vm = self.test_env.storage.get_node_instances('vm')[0]

        ephemeral_ip = vm['runtime_properties']['networkInterfaces'][0][
                'accessConfigs'][0]['natIP']

        self.assertIP(ephemeral_ip)


class GCPInstanceScriptTest(GCPTest, TestCase):
    blueprint_name = 'compute/startup-script-blueprint.yaml'

    inputs = (
            'project',
            'network',
            'zone',
            'gcp_auth',
            'image_id',
            )

    def assertions(self):
        self.assertIP(self.outputs['ip'], match="^10\..*")
