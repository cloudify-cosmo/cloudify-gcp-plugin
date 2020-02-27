########
# Copyright (c) 2015-2020 Cloudify Platform Ltd. All rights reserved
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

import os
from copy import copy
from abc import ABCMeta, abstractmethod, abstractproperty

from cloudify.workflows import local
from cloudify_cli import constants as cli_constants

from cosmo_tester.framework.testenv import (
        clear_environment,
        initialize_without_bootstrap,
        )


def setUp():
    initialize_without_bootstrap()


def tearDown():
    clear_environment()


class GCPTest(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def assertions(self):
        """This will be called after the deployment is finished.
        Put your test assertions here.
        The deployment is uninstalled during test teardown"""

    @abstractproperty
    def blueprint_name(self):
        """The path to the blueprint file, relative to
        `system_tests/resources`
        """

    @abstractproperty
    def inputs(self):
        """The list of inputs which should be copied from the provider context
        inputs to the deployment inputs for `blueprint`"""

    def setUp(self):
        super(GCPTest, self).setUp()

        self.ext_inputs = {
                k: self.env.cloudify_config[k]
                for k in self.inputs}

        blueprints_path = os.path.split(os.path.abspath(__file__))[0]
        blueprints_path = os.path.split(blueprints_path)[0]
        self.blueprints_path = os.path.join(
            blueprints_path,
            'resources',
        )

    def test_blueprint(self):
        blueprint = os.path.join(self.blueprints_path, self.blueprint_name)

        print('\n{}:test_blueprint starting....\n'.format(type(self).__name__))

        self.pre_install_hook()

        inputs = copy(self.ext_inputs)

        self.test_env = local.init_env(
            blueprint,
            inputs=inputs,
            name=self._testMethodName,
            ignored_modules=cli_constants.IGNORED_LOCAL_WORKFLOW_MODULES)

        self.addCleanup(
            self.test_env.execute,
            'uninstall',
            task_retries=10,
            task_retry_interval=3,
            )

        self.test_env.execute(
            'install',
            task_retries=10,
            task_retry_interval=3,
        )

        self.outputs = self.test_env.outputs()

        self.assertions()

        print('\n{}:test_blueprint succeded\n'.format(type(self).__name__))

    def pre_install_hook(self):
        "Override this if your test needs to do something before installing"

    def assertIP(self, ip, msg=None, match=None):
        """
        Set of assertions to valiate IPv4 addresses.
        optional `match` input is a regular expression which can be used to
        further constrain the allowed addresses.
        """
        parts = [int(n) for n in ip.split('.')]

        self.assertEqual(len(parts), 4)
        for i, part in enumerate(parts):
            part = int(part)
            self.assertLess(part, 256, 'part {} too big'.format(i))
            self.assertGreater(part, -1, 'part {} too small'.format(i))

        if match:
            self.assertRegexpMatches(ip, match)

    def get_instance(self, node):
        return self.test_env.storage.get_node_instances(node)[0]
