########
# Copyright (c) 2014 GigaSpaces Technologies Ltd. All rights reserved
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


def get_item_from_gcp_response(name, items):
    """
    Get item from GCP REST response JSON list by name
    :param name: item name
    :param items: list of items(dictionaries)
    :return: item if found in collection, None otherwise
    """
    for item in items.get('items', []):
        if item.get('name') == name:
            return item
    return None


def get_firewall_rule_name(network, firewall):
    """
    Prefix firewall rule name with network name
    :param network: name of the network the firewall rule is connected to
    :param firewall: the firewall rule name
    :return: network prefixed firewall rule name
    """
    return '{0}-{1}'.format(network, firewall['name'])


def get_instance_name(node_name):
    """
    Create GCP accepted instance name. From GCP specification:
    "Specifically, the name must be 1-63 characters long and match the regular
    expression [a-z]([-a-z0-9]*[a-z0-9])? which means the first character must
    be a lowercase letter, and all following characters must be a dash,
    lowercase letter, or digit, except the last character,
    which cannot be a dash."
    :param node_name: name given in blueprint(could have underscore)
    :return: GCP accepted instance name
    """
    return node_name.replace('_', '-')
