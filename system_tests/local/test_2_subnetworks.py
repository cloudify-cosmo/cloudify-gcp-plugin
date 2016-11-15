########
# Copyright (c) 2016 GigaSpaces Technologies Ltd. All rights reserved
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

import os
from copy import copy

from cloudify.workflows import local
from cloudify_cli import constants as cli_constants

from cosmo_tester.framework.testenv import TestCase

from . import GCPTest


class GCP2SubnetTest(GCPTest, TestCase):
    """
    This test involves use_external_resource so the "external" resources are
    set up in the first blueprint in the local overridden setUp() method.
    """

    pre_blueprint_name = 'networks/external-networks-setup.yaml'
    blueprint_name = 'networks/external-networks-blueprint.yaml'

    inputs = {
            'prefix',
            'gcp_auth',
            'project',
            'zone',
            }

    main_inputs = {
            'prefix',
            'project',
            'gcp_auth',
            'network',
            'subnet_1_name',
            'subnet_2_name',
            }

    def setUp(self):
        super(GCP2SubnetTest, self).setUp()

        self.logger.info('Creating a new Network')

        inputs = copy(self.ext_inputs)

        blueprint = os.path.join(self.blueprints_path, self.pre_blueprint_name)

        self.pre_setup_env = local.init_env(
            blueprint,
            inputs=inputs,
            name='external-networks-setup',
            ignored_modules=cli_constants.IGNORED_LOCAL_WORKFLOW_MODULES)

        self.pre_install_hook()

        self.addCleanup(
            self.pre_setup_env.execute,
            'uninstall',
            task_retries=10,
            task_retry_interval=3,
            )

        self.pre_setup_env.execute(
            'install',
            task_retries=10,
            task_retry_interval=3,
        )

        self.pre_outputs = self.pre_setup_env.outputs()

        self.ext_inputs = {
                k: self.pre_outputs.get(k) or self.env.cloudify_config[k]
                for k in self.main_inputs}

    def assertions(self):

        # For each Instance, assert that the Instance's network interface is in
        # the corresponding SubNetwork.
        for i in (1, 2):
            self.assertEqual(
                    self.outputs['subnet_{}_url'.format(i)],
                    self.outputs['instance_{}_subnet_url'.format(i)])
