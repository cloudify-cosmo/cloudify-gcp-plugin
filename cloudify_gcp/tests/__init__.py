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

import unittest

from mock import Mock

from cloudify.state import current_ctx
from cloudify.manager import DirtyTrackingDict


def ctx_mock():
    ctx = Mock()
    ctx.node.name = 'name'
    ctx.node.id = 'id'
    ctx.node.properties = {
        'agent_config': {'install_method': 'none'},
        'gcp_config': {
            'auth': {
                'type': 'service_account',
                'client_email': 'nobody@invalid',
                'private_key_id': "This isn't even an ID!",
                'private_key': 'nope!'
                },
            'zone': 'a very fake zone',
            'network': 'not a real network',
            'project': 'not really a project',
            },
        }
    ctx.instance.runtime_properties = DirtyTrackingDict()
    ctx.instance.relationships = []
    return ctx


class TestGCP(unittest.TestCase):

    def setUp(self):
        super(TestGCP, self).setUp()

        self.ctxmock = ctx_mock()
        current_ctx.set(self.ctxmock)
