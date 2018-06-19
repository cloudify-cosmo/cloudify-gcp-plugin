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
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os

from Crypto.PublicKey import RSA

from cloudify import ctx
from cloudify.decorators import operation
from cloudify.exceptions import NonRecoverableError

from .. import constants
from .. import utils
from ..gcp import (
        GCPError,
        check_response,
        GoogleCloudPlatform,
        )


class KeyPair(GoogleCloudPlatform):
    KEY_NAME = 'key'
    KEY_VALUE = 'sshKeys'

    def __init__(self,
                 config,
                 logger,
                 user,
                 private_key_path,
                 public_key_path):
        """
        Create KeyPair object

        :param config: gcp auth file
        :param logger: logger object
        :param user: name of the user to authenticate
        :param private_key_path: path where private key is stored
        """
        super(KeyPair, self).__init__(config, logger, None)
        self.user = user
        self.private_key_path = os.path.expanduser(private_key_path)
        self.public_key_path = public_key_path
        self.public_key = ''
        self.private_key = ''

    def create(self):
        """
        Create keypair: private and public key.

        """
        key = RSA.generate(2048)
        self.private_key = key.exportKey('PEM')
        self.public_key = key.exportKey('OpenSSH')

    def save_private_key(self):
        """
        Save private key to given path.

        """
        self.logger.info(
            'Save private key to {0}'.format(self.private_key_path))
        with open(self.private_key_path, 'w') as content_file:
            os.chmod(self.private_key_path, 0o600)
            content_file.write(self.private_key)

    @check_response
    def add_project_ssh_key(self):
        """
        Update project SSH private key. Add new key to project's
        common instance metadata.

        :return: REST response with operation responsible for the sshKeys
        addition to project metadata process and its status
        """
        common_instance_metadata = self.get_common_instance_metadata()
        if common_instance_metadata.get('items') is None:
            item = [{self.KEY_NAME: self.KEY_VALUE,
                    'value': utils.get_key_user_string(self.user,
                                                       self.public_key)}]
            common_instance_metadata['items'] = item
        else:
            item = utils.get_item_from_gcp_response(
                self.KEY_NAME,
                self.KEY_VALUE,
                common_instance_metadata)
            key = utils.get_key_user_string(self.user, self.public_key)
            if key not in item['value']:
                item['value'] = '{0}\n{1}'.format(item['value'], key)
        self.logger.info(
            'Add sshKey {0} to project {1} metadata'.format(
                self.public_key,
                self.project))
        return self.discovery.projects().setCommonInstanceMetadata(
            project=self.project,
            body=common_instance_metadata).execute()

    def remove_private_key(self):
        """
        Remove private key from file system.
        In case IOError throws GCPError with relevant message.
        """
        try:
            os.unlink(self.private_key_path)
        except IOError as e:
            self.logger.error(str(e))
            raise GCPError(str(e))


@operation
@utils.throw_cloudify_exceptions
def create(user,
           private_key_path,
           public_key_path,
           **kwargs):
    gcp_config = utils.get_gcp_config()
    keypair = KeyPair(gcp_config,
                      ctx.logger,
                      user,
                      private_key_path,
                      public_key_path)
    create_keypair(keypair)
    ctx.instance.runtime_properties[constants.USER] = user
    ctx.instance.runtime_properties[constants.PRIVATE_KEY] = \
        keypair.private_key
    ctx.instance.runtime_properties[constants.PUBLIC_KEY] = keypair.public_key
    if not utils.should_use_external_resource():
        if not user:
            raise NonRecoverableError(
                    'empty user string not allowed for newly created key')
        keypair.save_private_key()


def create_keypair(keypair):
    if utils.should_use_external_resource():
        keypair.private_key = ctx.get_resource(keypair.private_key_path)
        keypair.public_key = ctx.get_resource(
                os.path.expanduser(keypair.public_key_path))
        ctx.instance.runtime_properties[
            constants.RESOURCE_ID] = keypair.public_key
    else:
        keypair.create()


@operation
@utils.retry_on_failure('Retrying deleting keypair')
@utils.throw_cloudify_exceptions
def delete(user, private_key_path, **kwargs):
    gcp_config = utils.get_gcp_config()
    keypair = KeyPair(gcp_config,
                      ctx.logger,
                      user,
                      private_key_path,
                      None)
    keypair.public_key = ctx.instance.runtime_properties[constants.PUBLIC_KEY]
    ctx.instance.runtime_properties.pop(constants.PRIVATE_KEY, None)
    ctx.instance.runtime_properties.pop(constants.PUBLIC_KEY, None)
    ctx.instance.runtime_properties.pop(constants.RESOURCE_ID, None)
