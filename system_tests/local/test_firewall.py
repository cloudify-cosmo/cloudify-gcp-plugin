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

from cosmo_tester.framework.testenv import TestCase

from . import GCPTest


class GCPFirewallTest(GCPTest, TestCase):
    blueprint_name = 'firewall/simple-blueprint.yaml'

    inputs = (
            'project',
            'network',
            'zone',
            'gcp_auth',
            'image_id',
            )

    def assertions(self):
        """TODO: assert some stuff"""
        self.assertEqual(
                'aname',
                self.test_env.storage.get_node_instances(
                    'named_rule')[0].runtime_properties['name'])


class GCPSecurityGroupTest(GCPTest, TestCase):
    blueprint_name = 'firewall/securitygroup-blueprint.yaml'

    inputs = (
            'project',
            'network',
            'zone',
            'gcp_auth',
            'image_id',
            )

    def assertions(self):
        rules = self.test_env.storage.get_node_instances('sec_group')[0][
                'runtime_properties']['rules']

        sg_name = rules[0]['targetTags'][0]

        rule_invariants = {
            '{}-from-00000-to-tcp8080'.format(sg_name): {
                    'allowed': [
                        {'IPProtocol': 'tcp'}],
                    'sourceRanges': ['0.0.0.0/0'],
                    'targetTags': [sg_name],
                    },
            '{}-from-1234-to-udpnonetcpnone'.format(sg_name): {
                    'allowed': [
                        {u'IPProtocol': u'udp'},
                        {u'IPProtocol': u'tcp'}],
                    'sourceRanges': ['1.2.3.4'],
                    'targetTags': [sg_name],
                    },
            }

        for rule in rules:
            for k, v in rule_invariants[rule['name']].items():
                self.assertEqual(v, rule[k])
