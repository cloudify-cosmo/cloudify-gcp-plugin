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

from plugin.gcp.service import GoogleCloudPlatform
from plugin.gcp import utils


class TestService(unittest.TestCase):
    def setUp(self):  # noqa
        self.ctx = MockCloudifyContext()
        current_ctx.set(self.ctx)
        with open('inputs2.yaml') as f:
            self.config = yaml.safe_load(f).get('config')

    def test_create_network(self):
        gcp = GoogleCloudPlatform(self.config['auth'],
                                  self.config['project'],
                                  self.config['scope'],
                                  self.ctx.logger)
        networks = gcp.list_networks()
        item = utils.get_item_from_gcp_response(
            'name', self.config['network'], networks)
        self.assertIsNone(item)

        response = gcp.create_network(self.config['network'])
        gcp.wait_for_operation(response['name'], True)

        networks = gcp.list_networks()
        item = utils.get_item_from_gcp_response(
            'name', self.config['network'], networks)
        self.assertIsNotNone(item)

        response = gcp.delete_network(self.config['network'])
        gcp.wait_for_operation(response['name'], True)
        networks = gcp.list_networks()
        item = utils.get_item_from_gcp_response(
            'name', self.config['network'], networks)
        self.assertIsNone(item)

    def test_create_firewall_rule(self):
        gcp = GoogleCloudPlatform(self.config['auth'],
                                  self.config['project'],
                                  self.config['scope'],
                                  self.ctx.logger)
        networks = gcp.list_networks()
        item = utils.get_item_from_gcp_response(
            'name', self.config['network'], networks)
        self.assertIsNone(item)

        firewall_rules = gcp.list_firewall_rules()
        item = utils.get_item_from_gcp_response(
            'name', self.config['firewall']['name'], firewall_rules)
        self.assertIsNone(item)

        response = gcp.create_network(self.config['network'])
        gcp.wait_for_operation(response['name'], True)

        networks = gcp.list_networks()
        item = utils.get_item_from_gcp_response(
            'name', self.config['network'], networks)
        self.assertIsNotNone(item)

        response = gcp.create_firewall_rule(self.config['network'],
                                            self.config['firewall'])
        gcp.wait_for_operation(response['name'], True)

        firewall_rules = gcp.list_firewall_rules()
        item = utils.get_item_from_gcp_response(
            'name',
            utils.get_firewall_rule_name(
                self.config['network'],
                self.config['firewall']),
            firewall_rules)
        self.assertIsNotNone(item)

        response = gcp.delete_firewall_rule(self.config['network'],
                                            self.config['firewall'])

        gcp.wait_for_operation(response['name'], True)
        firewall_rules = gcp.list_firewall_rules()
        item = utils.get_item_from_gcp_response(
            'name',
            self.config['firewall']['name'],
            firewall_rules)
        self.assertIsNone(item)

        response = gcp.delete_network(self.config['network'])
        gcp.wait_for_operation(response['name'], True)
        networks = gcp.list_networks()
        item = utils.get_item_from_gcp_response(
            'name', self.config['network'], networks)
        self.assertIsNone(item)
