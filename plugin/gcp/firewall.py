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


class FirewallRule(object):
    SOURCE_TAGS = 'sourceTags'
    SOURCE_RANGES = 'sourceRanges'
    TARGET_TAGS = 'targetTags'
    ALLOWED = 'allowed'
    IPPROTOCOL = 'IPProtocol'
    PORTS = 'ports'

    def __init__(self, firewall):
        self.firewall = firewall

    def add_sourceTag(self, tag):
        sourceTags = self.firewall.get('sourceTags', [])
        self.firewall[self.SOURCE_TAGS] = sourceTags.append(tag)

    def remove_sourceTag(self, tag):
        sourceTags = self.firewall.get('sourceTags', [])
        sourceTags.remove(tag)  # error if not there

    def add_targetTag(self, tag):
        sourceTags = self.firewall.get('targetTags', [])
        sourceTags.append(tag)

    def remove_targetTag(self, tag):
        sourceTags = self.firewall.get('targetTags', [])
        sourceTags.remove(tag)  # error if not there

    def add_sourceRanges(self, cidr_family):
        sourceTags = self.firewall.get('sourceRanges', [])
        sourceTags.append(cidr_family)

    def add_allowed(self, protocol, ports):
        allowed = self.firewall.get(self.ALLOWED, [])
        allowed.append(di)
        self.firewall[self.ALLOWED] = allowed.append(allowed)

