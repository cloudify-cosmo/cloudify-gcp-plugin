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

from plugin.gcp import resources
from plugin.gcp import utils


class TestService(unittest.TestCase):
    def setUp(self):  # noqa
        self.ctx = MockCloudifyContext()
        current_ctx.set(self.ctx)
        with open('inputs_service.yaml') as f:
            self.config = yaml.safe_load(f).get('config')

    def test_create_network(self):
        network = resources.Network(self.config['auth'],
                                    self.config['project'],
                                    self.ctx.logger,
                                    self.config['network'])
        networks = network.list()
        item = utils.get_item_from_gcp_response(
            'name', self.config['network'], networks)
        self.assertIsNone(item)

        network.create()

        networks = network.list()
        item = utils.get_item_from_gcp_response(
            'name', self.config['network'], networks)
        self.assertIsNotNone(item)

        network.delete()

        networks = network.list()
        item = utils.get_item_from_gcp_response(
            'name', self.config['network'], networks)
        self.assertIsNone(item)

    def test_create_firewall_rule(self):
        network = resources.Network(self.config['auth'],
                                    self.config['project'],
                                    self.ctx.logger,
                                    self.config['network'])
        networks = network.list()
        item = utils.get_item_from_gcp_response(
            'name', self.config['network'], networks)
        self.assertIsNone(item)

        firewall = resources.FirewallRule(self.config['auth'],
                                          self.config['project'],
                                          self.ctx.logger,
                                          self.config['firewall'],
                                          self.config['network'])
        firewall_rules = firewall.list()
        item = utils.get_item_from_gcp_response('name',
                                                firewall.name,
                                                firewall_rules)
        self.assertIsNone(item)

        network.create()

        networks = network.list()
        item = utils.get_item_from_gcp_response(
            'name', self.config['network'], networks)
        self.assertIsNotNone(item)

        firewall.create()

        firewall_rules = firewall.list()
        item = utils.get_item_from_gcp_response(
            'name',
            firewall.name,
            firewall_rules)
        self.assertIsNotNone(item)

        firewall.delete()

        firewall_rules = firewall.list()
        item = utils.get_item_from_gcp_response(
            'name',
            firewall.name,
            firewall_rules)
        self.assertIsNone(item)

        network.delete()

        networks = network.list()
        item = utils.get_item_from_gcp_response(
            'name', self.config['network'], networks)
        self.assertIsNone(item)

    def test_tag_instance(self):
        test_tag = 'agent-123'
        name = 'name'
        instance = resources.Instance(self.config['auth'],
                                      self.config['project'],
                                      self.ctx.logger,
                                      instance_name=name,
                                      image=self.config['agent_image'],
                                      tags=[test_tag])

        instance.create()
        instances = instance.list()
        item = utils.get_item_from_gcp_response('name', name, instances)
        tag = find_in_list(test_tag, item['tags'].get('items'))
        self.assertIsNotNone(tag)

        instance.delete()

        instance.tags = []
        instance.create()
        instances = instance.list()
        item = utils.get_item_from_gcp_response('name', name, instances)
        tags = item.get('tags', [])
        tag = find_in_list(test_tag, tags.get('items', []))
        self.assertIsNone(tag)

        instance.set_tags([test_tag])
        instances = instance.list()
        item = utils.get_item_from_gcp_response('name', name, instances)
        tag = find_in_list(test_tag, item['tags'].get('items'))
        self.assertIsNotNone(tag)

        instance.delete()


def find_in_list(what, list):
    for item in list:
        if item == what:
            return item
    return None
