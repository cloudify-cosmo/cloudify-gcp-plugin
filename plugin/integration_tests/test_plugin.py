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
#    * See the License for the specific language governing permissions and
#    * limitations under the License.

import os
import unittest

from cloudify.mocks import MockCloudifyContext
from cloudify.state import current_ctx
from cloudify.workflows import local
from cloudify import ctx
import yaml

from plugin.gcp.resources import Instance


class TestPlugin(unittest.TestCase):
    inputs = None

    def setUp(self):  # noqa
        ctx = MockCloudifyContext(node_id='id', node_name='name')
        current_ctx.set(ctx)
        ctx.logger.info('Setting environment')

        # build blueprint path
        blueprint_path = os.path.join(os.path.dirname(__file__),
                                      'blueprint', 'blueprint.yaml')
        with open('inputs_plugin.yaml') as f:
            self.inputs = yaml.safe_load(f)

        # setup local workflow execution environment
        self.env = local.init_env(blueprint_path,
                                  name=self._testMethodName,
                                  inputs=self.inputs)

    def test_create_instance(self):
        config = self.inputs['config']
        config_instance = self.inputs['instance']
        instance = Instance(config,
                            ctx.logger,
                            instance_name=ctx.instance.id,
                            image=config_instance['image'])
        instances = instance.list()
        base = len(instances.get('items', []))
        ctx.logger.info('Install workflow')
        # execute install workflow
        self.env.execute('install', task_retries=0)

        ctx.logger.info('Check instance number')
        instances = instance.list()
        self.assertEqual(len(instances['items']), base + 1)

        ctx.logger.info('Uninstall workflow')
        self.env.execute('uninstall', task_retries=0)

        ctx.logger.info('Check instance number')
        instances = instance.list()
        self.assertEqual(len(instances.get('items', [])), base)
