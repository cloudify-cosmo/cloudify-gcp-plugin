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

from plugin.gcp.firewall import FirewallRule
from plugin.gcp.instance import Instance
from plugin.gcp.network import Network
from plugin.gcp import utils


class TestService(unittest.TestCase):
    def setUp(self):  # noqa
        self.ctx = MockCloudifyContext()
        current_ctx.set(self.ctx)
        with open('inputs_service.yaml') as f:
            self.config = yaml.safe_load(f)

    def test_create_network(self):
        network = Network(self.config['config'],
                          self.ctx.logger,
                          self.config['network'])
        networks = network.list()
        item = utils.get_item_from_gcp_response(
            'name', network.name, networks)
        self.assertIsNone(item)
        self.ctx.logger.info(str(network.create))
        network.create()

        networks = network.list()
        item = utils.get_item_from_gcp_response(
            'name', network.name, networks)
        self.assertIsNotNone(item)

        network.delete()

        networks = network.list()
        item = utils.get_item_from_gcp_response(
            'name', self.config['network']['name'], networks)
        self.assertIsNone(item)

    def test_create_firewall_rule(self):
        network = Network(self.config['config'],
                          self.ctx.logger,
                          self.config['network'])
        networks = network.list()
        item = utils.get_item_from_gcp_response(
            'name', self.config['network']['name'], networks)
        self.assertIsNone(item)

        firewall = FirewallRule(self.config['config'],
                                self.ctx.logger,
                                self.config['firewall'],
                                self.config['config']['network'])
        firewall_rules = firewall.list()
        item = utils.get_item_from_gcp_response('name',
                                                firewall.name,
                                                firewall_rules)
        self.assertIsNone(item)

        network.create()

        networks = network.list()
        item = utils.get_item_from_gcp_response(
            'name', self.config['network']['name'], networks)
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
            'name', self.config['network']['name'], networks)
        self.assertIsNone(item)

    def test_tag_instance(self):
        test_tag = 'agent-123'
        name = 'name'
        self.config['config']['network'] = 'default'
        instance = Instance(self.config['config'],
                            self.ctx.logger,
                            instance_name=name,
                            image=self.config['instance']['image'],
                            tags=[test_tag],
                            machine_type=self.config['instance_type'])

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

    def test_tag_firewall(self):
        network = Network(self.config['config'],
                          self.ctx.logger,
                          self.config['network'])
        network.create()

        firewall_rule = dict(self.config['firewall'])
        source_tag = 'source-tag'
        target_tag = 'target-tag'
        firewall_rule['sourceTags'] = [source_tag]
        firewall_rule['targetTags'] = [target_tag]
        firewall = FirewallRule(self.config['config'],
                                self.ctx.logger,
                                firewall_rule,
                                self.config['config']['network'])
        firewall.create()
        firewall_name = firewall.name
        firewalls = firewall.list()
        item = utils.get_item_from_gcp_response('name',
                                                firewall_name,
                                                firewalls)
        self.assertEqual(source_tag, find_in_list(source_tag,
                                                  item['sourceTags']))
        self.assertEqual(target_tag, find_in_list(target_tag,
                                                  item['targetTags']))

        firewall.firewall = self.config['firewall']
        firewall.firewall['name'] = firewall_name
        firewall.update()
        firewalls = firewall.list()
        item = utils.get_item_from_gcp_response('name',
                                                firewall_rule['name'],
                                                firewalls)
        self.assertIsNone(find_in_list(source_tag, item.get('sourceTags', [])))
        self.assertIsNone(find_in_list(target_tag, item.get('targetTags', [])))

        firewall.firewall = firewall_rule
        firewall.firewall['name'] = firewall_name
        firewall.update()
        firewalls = firewall.list()
        item = utils.get_item_from_gcp_response('name',
                                                firewall_rule['name'],
                                                firewalls)
        self.assertEqual(source_tag, find_in_list(source_tag,
                                                  item['sourceTags']))
        self.assertEqual(target_tag, find_in_list(target_tag,
                                                  item['targetTags']))
        firewall.delete()
        network.delete()


def find_in_list(what, list):
    for item in list:
        if item == what:
            return item
    return None
