# #######
# Copyright (c) 2014 GigaSpaces Technologies Ltd. All rights reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
#    * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    * See the License for the specific language governing permissions and
#    * limitations under the License.

import unittest

from cloudify.mocks import MockCloudifyContext
from cloudify.state import current_ctx

from plugin.gcp import service


class TestService(unittest.TestCase):
    # inject input from test
    config = {
        'client_secret': '/tmp/blueprint_resources/client_secret.json',
        #put absolute path to client_secret.json
        'gcp_scope': 'https://www.googleapis.com/auth/compute',
        'storage': '/tmp/blueprint_resources/oauth.dat',
        #put absolute path to oauth.dat
        'project': '',
        'zone': 'us-central1-f',
        'network': 'test-network'
    }

    def setUp(self):
        ctx = MockCloudifyContext()
        current_ctx.set(ctx)

    def test_create_network(self):
        flow = service.init_oauth(self.config)
        credentials = service.authenticate(
            flow, self.config['storage'])
        compute = service.compute(credentials)
        networks = service.list_networks(compute,
                                         self.config['project'])
        item = service._get_item_from_list(
            self.config['network'],
            networks)
        self.assertIsNone(item)

        response = service.create_network(compute,
                                          self.config['project'],
                                          self.config['network'])
        service.wait_for_operation(compute,
                                   self.config,
                                   response['name'],
                                   True)

        networks = service.list_networks(compute,
                                         self.config['project'])
        item = service._get_item_from_list(
            self.config['network'],
            networks)
        self.assertIsNotNone(item)

        response = service.delete_network(
            compute,
            self.config['project'],
            self.config['network'])
        service.wait_for_operation(compute,
                                   self.config,
                                   response['name'],
                                   True)
        networks = service.list_networks(compute,
                                         self.config['project'])
        item = service._get_item_from_list(
            self.config['network'],
            networks)
        self.assertIsNone(item)
