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

from plugin import gcp

class TestPlugin(unittest.TestCase):
    inputs = None

    def setUp(self):
        ctx = MockCloudifyContext()
        current_ctx.set(ctx)
        ctx.logger.info("Setting environment")

        # build blueprint path
        blueprint_path = os.path.join(os.path.dirname(__file__),
                                      'blueprint', 'blueprint.yaml')

        # inject input from test
        self.inputs = {'config':
                           {
                               'client_secret': '/tmp/blueprint_resources/client_secret.json',  #put absolute path to client_secret.json
                               'gcp_scope': 'https://www.googleapis.com/auth/compute',
                               'agent_image': '/projects/ubuntu-os-cloud/global/images/ubuntu-1204-precise-v20150316',
                               'storage': '/tmp/blueprint_resources/oauth.dat',  #put absolute path to oauth.dat
                               'project': 'ruckuseurope',
                               'zone': 'us-central1-f'
                           }}

        # setup local workflow execution environment
        self.env = local.init_env(blueprint_path,
                                  name=self._testMethodName,
                                  inputs=self.inputs)

    def test_my_task(self):
        ctx.logger.info("Check initial instance number")

        flow = gcp.service.init_oauth(self.inputs['config'])
        credentials = gcp.service.authenticate(
            flow, self.inputs['config']['storage'])
        compute = gcp.service.compute(credentials)

        instances = gcp.service.list_instances(self.inputs['config'], compute)
        initial = len(instances['items']) if instances.get('items') else 0

        ctx.logger.info("Install workflow")
        # execute install workflow
        self.env.execute('install', task_retries=0)

        ctx.logger.info("Check instance number")
        instances = gcp.service.list_instances(self.inputs['config'], compute)
        self.assertEqual(len(instances['items']), initial + 1)

        ctx.logger.info("Uninstall workflow")
        self.env.execute('uninstall', task_retries=0)

        ctx.logger.info("Check instance number")
        instances = gcp.service.list_instances(self.inputs['config'], compute)
        size = len(instances['items']) if instances.get('items') else 0
        self.assertEqual(size, initial)
