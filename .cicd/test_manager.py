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

PLUGIN_NAME = 'cloudify-azure-plugin'
DEVELOPMENT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(
        os.path.realpath(__file__)), '../..'))
TEST_KEY_PATH = '/tmp/foo.rsa'
TEST_PUB_PATH = '/tmp/foo.rsa.pub'
GCP_KEY_PATH = '/tmp/gcp_private_key'
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
            'region': os.getenv('gcp_region'),
            'network_name': '{0}network'.format(test_id),
            'subnet_name': '{0}subnet'.format(test_id)
        }

    def create_secrets(self):
        secrets = {
            'agent_key_private': os.getenv('agent_key_private',
                                           open(TEST_KEY_PATH).read()),
            'agent_key_public': os.getenv('agent_key_public',
                                          open(TEST_PUB_PATH).read()),
            'gcp_region': os.getenv('gcp_region'),
            'gcp_zone': os.getenv('gcp_zone'),
            'gcp_private_key': open(GCP_KEY_PATH).read(),
            'gcp_private_key_id': os.getenv('gcp_private_key_id'),
            'gcp_project_id': os.getenv('gcp_project_id'),
            'gcp_client_id': os.getenv('gcp_client_id'),
            'gcp_client_email': os.getenv('gcp_client_email'),
            'gcp_client_x509_cert_url': os.getenv('gcp_client_x509_cert_url'),
        }
        self._create_secrets(secrets)

    def upload_plugins(self):
        self.upload_mock_plugin(
            PLUGIN_NAME, self.plugin_root_directory)
        self.upload_mock_plugin(
            'cloudify-utilities-plugin',
            os.path.join(DEVELOPMENT_ROOT, 'cloudify-utilities-plugin'))
        self.upload_mock_plugin(
            'cloudify-ansible-plugin',
            os.path.join(DEVELOPMENT_ROOT, 'cloudify-ansible-plugin'))

    def test_blueprints(self):
        self.upload_plugins()
        self.create_secrets()
        self.check_hello_world_blueprint('gcp', self.inputs, 400)
        self.check_db_lb_app_blueprint(
            'gcp', 800,
            {
                'resource_prefix': 'dblbapp',
                'resource_suffix': test_id
            }
        )
