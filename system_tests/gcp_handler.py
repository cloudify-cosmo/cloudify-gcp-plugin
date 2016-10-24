########
# Copyright (c) 2015 GigaSpaces Technologies Ltd. All rights reserved
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

import copy
from time import sleep
from contextlib import contextmanager

from cosmo_tester.framework.handlers import (
    BaseHandler,
    BaseCloudifyInputsConfigReader)


class GCPCleanupContext(BaseHandler.CleanupContext):
    def __init__(self, context_name, env):
        super(GCPCleanupContext, self).__init__(context_name, env)
        #self.before_run = self.env.handler.gcp_infra_state()

    @classmethod
    def clean_resources(cls, env, resources):

        return
        # TODO: Probably want to remove this stuff
        cls.logger.info('Performing cleanup: will try removing these '
                        'resources: {0}'
                        .format(resources))

        failed_to_remove = {}

        for segment in range(6):
            failed_to_remove = \
                env.handler.remove_gcp_resources(resources)
            if not failed_to_remove:
                break

        cls.logger.info('Leftover resources after cleanup: {0}'
                        .format(failed_to_remove))

        return failed_to_remove

    def cleanup(self):
        super(GCPCleanupContext, self).cleanup()
        resources_to_teardown = self.get_resources_to_teardown()
        if self.skip_cleanup:
            self.logger.warn('[{0}] SKIPPING cleanup: of the resources: {1}'
                             .format(self.context_name, resources_to_teardown))
            return

        self.clean_resources(self.env, resources_to_teardown)

    def get_resources_to_teardown(self):
        return
        # TODO: Probably want to remove this stuff
        current_state = self.env.handler.gcp_infra_state()
        return self.env.handler.gcp_infra_state_delta(
            before=self.before_run, after=current_state)

    @classmethod
    def clean_all(cls, env):
        resources_to_be_removed = env.handler.gcp_infra_state()
        cls.logger.info(
            "Current resources in account:"
            " {0}".format(resources_to_be_removed))
        if env.use_existing_manager_keypair:
            resources_to_be_removed['key_pairs'].pop(
                env.management_keypair_name, None)
        if env.use_existing_agent_keypair:
            resources_to_be_removed['key_pairs'].pop(env.agent_keypair_name,
                                                     None)

        failed_to_remove = cls.clean_resources(env, resources_to_be_removed)


class CloudifyGCPInputsConfigReader(BaseCloudifyInputsConfigReader):

    @property
    def management_user_name(self):
        return self.config['ssh_user']

    @property
    def management_server_name(self):
        return self.config['manager_server_name']

    @property
    def agent_key_path(self):
        return self.config['agent_private_key_path']

    @property
    def management_key_path(self):
        return self.config['ssh_key_filename']

    @property
    def agent_keypair_name(self):
        return self.config['agent_keypair_name']

    @property
    def management_keypair_name(self):
        return self.config['manager_keypair_name']

    @property
    def agents_security_group(self):
        return self.config['agent_security_group_name']

    @property
    def management_security_group(self):
        return self.config['manager_security_group_name']

    @property
    def use_existing_manager_keypair(self):
        return self.config['use_existing_manager_keypair']

    @property
    def use_existing_agent_keypair(self):
        return self.config['use_existing_agent_keypair']

    @property
    def project(self):
        return self.config['project']

    @property
    def gcp_auth(self):
        return self.config['gcp_auth']

    @property
    def centos_7_image_user(self):
        return 'centos'


class GCPHandler(BaseHandler):
    CleanupContext = GCPCleanupContext
    CloudifyConfigReader = CloudifyGCPInputsConfigReader

    def gcp_client(self):
        credentials = self._client_credentials()
        return GCPConnection(**credentials)

    def remove_keypairs_from_local_env(self, env):
        """TODO: remove the keypairs"""

    @contextmanager
    def _handled_exception(self, resource_id, failed, resource_group):
        try:
            yield
        except BaseException as ex:
            failed[resource_group][resource_id] = ex


handler = GCPHandler
