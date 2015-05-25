# #######
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
import os
import tempfile

from Crypto.PublicKey import RSA

from plugin.gcp.service import GoogleCloudPlatform
from plugin.gcp.service import blocking
from plugin.gcp.service import GCPError
from plugin.gcp import utils


class KeyPair(GoogleCloudPlatform):
    KEY_NAME = 'key'
    KEY_VALUE = 'sshKeys'

    def __init__(self,
                 config,
                 logger,
                 user,
                 private_key_path):
        super(KeyPair, self).__init__(config, logger)
        self.user = user
        self.private_key_path = private_key_path
        self.public_key = ''
        self.private_key = ''

    def wait_for_operation(self, operation, global_operation=True):
        super(KeyPair, self).wait_for_operation(operation, global_operation)

    def create_keypair(self):
        key = RSA.generate(2048)
        self.private_key = key.exportKey('PEM')
        self.public_key = key.exportKey('OpenSSH')

    def save_private_key(self):
        with open(self.private_key_path, 'w') as content_file:
            os.chmod(self.private_key_path, 0600)
            content_file.write(self.private_key)

    @blocking(True)
    def add_project_ssh_key(self, user, ssh_key):
        """
        Update project SSH private key. Add new key to project's
        common instance metadata.
        Global operation.

        :param user: user the key belongs to
        :param ssh_key: key belonging to the user
        :return: REST response with operation responsible for the sshKeys
        addition to project metadata process and its status
        """
        self.logger.info('Update project sshKeys metadata')
        commonInstanceMetadata = self.get_common_instance_metadata()
        if commonInstanceMetadata.get('items') is None:
            item = [{self.KEY_NAME: self.KEY_VALUE,
                    'value': '{0}:{1}'.format(user, ssh_key)}]
            commonInstanceMetadata['items'] = item
        else:
            item = utils.get_item_from_gcp_response(
                self.KEY_NAME,
                self.KEY_VALUE,
                commonInstanceMetadata)
            key = '{0}:{1}'.format(user, ssh_key)
            if key not in item['value']:
                item['value'] = '{0}\n{1}'.format(item['value'], key)
        return self.compute.projects().setCommonInstanceMetadata(
            project=self.project,
            body=commonInstanceMetadata).execute()

    @blocking(True)
    def remove_project_ssh_key(self):
        """
        Update project SSH private key. Remove new key to project's
        common instance metadata.
        Global operation.

        :return: REST response with operation responsible for the sshKeys
        addition to project metadata process and its status
        """
        self.logger.info('Update project sshKeys metadata')
        commonInstanceMetadata = self.get_common_instance_metadata()
        if commonInstanceMetadata.get('items') is not None:
            item = utils.get_item_from_gcp_response(
                self.KEY_NAME,
                self.KEY_VALUE,
                commonInstanceMetadata)
            key = '{0}:{1}'.format(self.user, self.public_key)
            if key in item['value']:
                item['value'] = item['value'].replace(key, '')
        return self.compute.projects().setCommonInstanceMetadata(
            project=self.project,
            body=commonInstanceMetadata).execute()

    def remove_private_key(self):
        try:
            os.unlink(self.private_key_path)
        except IOError as e:
            self.logger.error(str(e))
            raise GCPError(str(e))
