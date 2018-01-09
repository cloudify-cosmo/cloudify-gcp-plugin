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
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
from os.path import basename

from cosmo_tester.framework.testenv import TestCase

from cloudify_gcp.gcp import GoogleCloudPlatform
from . import GCPTest


class GCPInstanceGroupTest(GCPTest, TestCase):
    blueprint_name = 'compute/instance-group-blueprint.yaml'

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

        conf = self.test_env.storage.get_nodes()[0]['properties']['gcp_config']
        attrs = self.test_env.storage.get_node_instances('instance_group')[0]

        gcp = GoogleCloudPlatform(
                config=conf,
                logger=logging.getLogger(),
                name='test',
                )

        response = gcp.discovery.instanceGroups().listInstances(
                project=conf['project'],
                zone=basename(attrs['runtime_properties']['zone']),
                instanceGroup=attrs['runtime_properties']['name'],
                body={},
                ).execute()

        self.assertEqual(
                response['items'][0]['instance'],
                self.test_env.storage.get_node_instances('vm')[0][
                    'runtime_properties']['selfLink'],
                )
