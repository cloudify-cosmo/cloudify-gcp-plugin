# #######
# Copyright (c) 2019 Cloudify Platform Ltd. All rights reserved
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
from random import random

from integration_tests.tests.test_cases import PluginsTest
from integration_tests.tests import utils as test_utils

PLUGIN_NAME = 'cloudify-gcp-plugin'

test_id = '{0}{1}'.format(
    os.getenv('CIRCLE_JOB', 'cfy'),
    os.getenv('CIRCLE_BUILD_NUM', str(random())[-4:-1])
)


class GCPPluginTestCase(PluginsTest):

    base_path = os.path.dirname(os.path.realpath(__file__))

    @property
    def plugin_root_directory(self):
        return os.path.abspath(os.path.join(self.base_path, '..'))

    @property
    def inputs(self):
        return {
            'gcp_region': os.getenv('gcp_region'),
            'gcp_zone': os.getenv('gcp_zone'),
            'gcp_private_key': os.getenv('gcp_private_key'),
            'gcp_private_key_id': os.getenv('gcp_private_key_id'),
            'gcp_project_id': os.getenv('gcp_project_id'),
            'gcp_client_id': os.getenv('gcp_client_id'),
            'gcp_client_email': os.getenv('gcp_client_email'),
            'gcp_client_x509_cert_url': os.getenv('gcp_client_x509_cert_url'),
            'network_name': '{0}network'.format(test_id),
            'subnet_name': '{0}subnet'.format(test_id)
        }

    def check_main_blueprint(self):
        blueprint_id = 'gcp_blueprint'
        self.addCleanup(self.undeploy_application, blueprint_id)
        dep, ex_id = self.deploy_application(
            test_utils.get_resource(
                os.path.join(
                    self.plugin_root_directory,
                    'blueprints/vm.yaml')),
            timeout_seconds=400,
            blueprint_id=blueprint_id,
            deployment_id=blueprint_id,
            inputs=self.inputs)
        self.undeploy_application(dep.id)

    def test_blueprints(self):
        self.upload_mock_plugin(PLUGIN_NAME, self.plugin_root_directory)
        self.check_main_blueprint()
