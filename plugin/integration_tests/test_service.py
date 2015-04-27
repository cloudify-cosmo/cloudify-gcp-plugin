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
# * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# * See the License for the specific language governing permissions and
# * limitations under the License.

from cloudify.mocks import MockCloudifyContext
from cloudify.state import current_ctx
import unittest
import yaml

from plugin.gcp import service


class TestService(unittest.TestCase):

    def setUp(self):  # noqa
        ctx = MockCloudifyContext()
        current_ctx.set(ctx)
        with open('inputs.yaml') as f:
            self.config = yaml.safe_load(f).get('config')

    def test_create_network(self):
        flow = service.init_oauth(self.config)
        credentials = service.authenticate(flow, self.config['storage'])
        compute = service.compute(credentials)
        networks = service.list_networks(compute, self.config)
        item = service._get_item_from_gcp_response(
            self.config['network'],
            networks)
        self.assertIsNone(item)

        response = service.create_network(compute, self.config)
        service.wait_for_operation(compute,
                                   self.config,
                                   response['name'],
                                   True)

        networks = service.list_networks(compute, self.config)
        item = service._get_item_from_gcp_response(
            self.config['network'],
            networks)
        self.assertIsNotNone(item)

        response = service.delete_network(compute, self.config)
        service.wait_for_operation(compute,
                                   self.config,
                                   response['name'],
                                   True)
        networks = service.list_networks(compute, self.config)
        item = service._get_item_from_gcp_response(
            self.config['network'],
            networks)
        self.assertIsNone(item)

    def test_create_firewall_rule(self):
        flow = service.init_oauth(self.config)
        credentials = service.authenticate(
            flow, self.config['storage'])
        compute = service.compute(credentials)
        networks = service.list_networks(compute, self.config)
        item = service._get_item_from_gcp_response(
            self.config['network'],
            networks)
        self.assertIsNone(item)

        firewall_rules = service.list_firewall_rules(compute, self.config)
        item = service._get_item_from_gcp_response(
            self.config['firewall']['name'],
            firewall_rules)
        self.assertIsNone(item)

        response = service.create_network(compute, self.config)
        service.wait_for_operation(compute,
                                   self.config,
                                   response['name'],
                                   True)

        networks = service.list_networks(compute, self.config)
        item = service._get_item_from_gcp_response(
            self.config['network'],
            networks)
        self.assertIsNotNone(item)

        response = service.create_firewall_rule(compute, self.config)
        service.wait_for_operation(compute,
                                   self.config,
                                   response['name'],
                                   True)

        firewall_rules = service.list_firewall_rules(compute, self.config)
        item = service._get_item_from_gcp_response(
            self.config['firewall']['name'],
            firewall_rules)
        self.assertIsNotNone(item)

        response = service.delete_firewall_rule(compute, self.config)
        service.wait_for_operation(compute,
                                   self.config,
                                   response['name'],
                                   True)
        firewall_rules = service.list_firewall_rules(compute, self.config)
        item = service._get_item_from_gcp_response(
            self.config['firewall']['name'],
            firewall_rules)
        self.assertIsNone(item)

        response = service.delete_network(compute, self.config)
        service.wait_for_operation(compute,
                                   self.config,
                                   response['name'],
                                   True)
        networks = service.list_networks(compute, self.config)
        item = service._get_item_from_gcp_response(self.config, networks)
        self.assertIsNone(item)
