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

from cosmo_tester.framework.testenv import TestCase

from . import GCPTest


class GCPSimpleNetworkTest(GCPTest, TestCase):
    blueprint_name = 'networks/simple-blueprint.yaml'

    inputs = {
            'gcp_auth',
            'project',
            'network',
            'zone',
            }

    def assertions(self):
        pass


class GCPNetAndSubnetTest(GCPTest, TestCase):
    blueprint_name = 'networks/net-and-subnet-blueprint.yaml'

    inputs = {
            'gcp_auth',
            'project',
            'zone',
            }

    def assertions(self):

        storage = self.test_env.storage
        simple_network = storage.get_node_instances('simple-network')[0]
        simple_subnet_a = storage.get_node_instances('simple-subnet_a')[0]
        simple_subnet_b = storage.get_node_instances('simple-subnet_b')[0]

        for ex, ac in (
            ('networkname', simple_network['runtime_properties']['name']),
            (False,
                simple_network['runtime_properties'][
                    'autoCreateSubnetworks']),
            ('10.11.12.0/22', simple_subnet_a['runtime_properties'][
                'ipCidrRange']),
            ('10.11.16.0/22', simple_subnet_b['runtime_properties'][
                'ipCidrRange']),

            ('networkname', self.test_env.outputs()['simple-network']),
        ):
            self.assertEqual(ex, ac)
