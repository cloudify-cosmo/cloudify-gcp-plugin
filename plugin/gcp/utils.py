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
import re

MAX_GCP_INSTANCE_NAME = 63
ID_HASH_CONST = 6
TARGET_TAGS = 'targetTags'
SOURCE_TAGS = 'sourceTags'


def get_item_from_gcp_response(key_field, key_name, items):
    """
    Get item from GCP REST response JSON list by name.
    items = [{ 'key_field': 'key_name', 'key_field_value': 'value'}]
    :param key_field: item dictionary key
    :param key_value: item dictionary value
    :param items: list of items(dictionaries)
    :return: item if found in collection, None otherwise
    """
    for item in items.get('items', []):
        if item.get(key_field) == key_name:
            return item
    return None


def get_gcp_resource_name(name):
    """
    Create GCP accepted name of resource. From GCP specification:
    "Specifically, the name must be 1-63 characters long and match the regular
    expression [a-z]([-a-z0-9]*[a-z0-9])? which means the first character must
    be a lowercase letter, and all following characters must be a dash,
    lowercase letter, or digit, except the last character,
    which cannot be a dash."
    :param name: name of resource to be given
    :return: GCP accepted instance name
    """
    # replace underscores with hyphens
    final_name = name.replace('_', '-')
    # remove all non-alphanumeric characters except hyphens
    final_name = re.sub(r'[^a-zA-Z0-9-]+', '', final_name)
    # assure the first character is alpha
    if not final_name[0].isalpha():
        final_name = '{0}{1}'.format('a', final_name)
    # trim to the length limit
    if len(final_name) > MAX_GCP_INSTANCE_NAME:
        remain_len = MAX_GCP_INSTANCE_NAME - len(final_name)
        final_name = '{0}{1}'.format(final_name[:remain_len - ID_HASH_CONST],
                                     final_name[-ID_HASH_CONST:])
    # convert string to lowercase
    return final_name.lower()


def get_firewall_rule_name(network, firewall):
    """
    Prefix firewall rule name with network name

    :return: network prefixed firewall rule name
    """
    name = '{0}-{1}'.format(network, firewall)
    return get_gcp_resource_name(name)
