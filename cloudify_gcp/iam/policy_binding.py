# #######
# Copyright (c) 2018-2020 Cloudify Platform Ltd. All rights reserved
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

from copy import deepcopy

from cloudify import ctx
from cloudify.decorators import operation
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2 import service_account

from .. import gcp
from .. import utils
from .. import constants

EMPTY_POLICY_BINDING = {'bindings': []}


class PolicyBinding(gcp.GoogleCloudPlatform):
    # https://cloud.google.com/resource-manager/reference/rest/v1/Policy
    # Example Gcloud Command:
    # gcloud iam service-accounts add-iam-policy-binding
    # [Service Account]
    # --member='user:[Service Account]'
    # --role=projects/[Project]/roles/[Role Name]

    def __init__(self, config, logger, resource, policy):
        super(gcp.GoogleCloudPlatform, self).__init__(
            config,
            logger,
            scope=constants.CLOUDRESOURCES_SCOPE,
            discovery=constants.CLOUDRESOURCES_DISCOVERY)
        self.resource = resource or config['project']
        self.new_policy = policy

    def get_credentials(self, *_, **__):
        return service_account.Credentials. \
            from_service_account_info(self.auth, always_use_jwt_access=True)

    def create_discovery(self, discovery, scope, api_version):
        """
        Create Google Cloud API discovery object and perform authentication.

        :param discovery: name of the API discovery to be created
        :param scope: scope the API discovery will have
        :param api_version: version of the API
        :return: discovery object
        :raise: GCPError if there is a problem with service account JSON file:
        e.g. the file is not under the given path or it has wrong permissions
        """
        try:
            credentials = self.get_credentials(scope)
            return build(discovery, api_version, credentials=credentials)
        except IOError as e:
            self.logger.error(str(e))
            raise gcp.GCPError(str(e))

    @gcp.check_response
    def get(self):
        request_body = {
            'options': {
                'requestedPolicyVersion': 3
            }
        }
        try:
            return self.discovery.projects().getIamPolicy(
                resource=self.resource, body=request_body).execute()
        except HttpError as e:
            self.logger.error(str(e))
            return EMPTY_POLICY_BINDING

    @gcp.check_response
    def create(self):
        # https://cloud.google.com/resource-manager/
        # reference/rest/v1/projects/setIamPolicy
        policy = self.add_new_policies_to_current_policy()
        self.logger.debug('Attempting to update policy {}'.format(policy))
        request_body = {
            'policy': policy
        }
        try:
            return self.discovery.projects().setIamPolicy(
                resource=self.resource,
                body=request_body).execute()
        except HttpError as e:
            error = str(e)
            self.logger.error(error)
            if '404' in error:
                return ctx.operation.retry(
                    message='Attempting to retry create policy binding: '
                            '{error}.'.format(error=error))
            else:
                raise

    @gcp.check_response
    def delete(self):
        # https://cloud.google.com/iam/docs/granting-changing-revoking-access
        policy = self.remove_new_policies_from_current_policy()
        if policy == EMPTY_POLICY_BINDING:
            return EMPTY_POLICY_BINDING
        self.logger.debug('Attempting to rollback policy {}'.format(policy))
        request_body = {
            'policy': policy
        }
        try:
            return self.discovery.projects().setIamPolicy(
                resource=self.resource,
                body=request_body).execute()
        except HttpError as e:
            error = str(e)
            self.logger.error(error)
            if '404' in error:
                return EMPTY_POLICY_BINDING
            else:
                raise

    def add_new_policies_to_current_policy(self):
        current_policy = deepcopy(self.get())
        for binding in self.new_policy['bindings']:
            if binding not in current_policy['bindings']:
                current_policy['bindings'].append(binding)
        return current_policy

    def remove_new_policies_from_current_policy(self):
        current_policy = self.get()
        for n, binding in enumerate(self.new_policy['bindings']):
            if binding in current_policy['bindings']:
                del current_policy['bindings'][n]
        return current_policy


@operation(resumable=True)
@utils.throw_cloudify_exceptions
def create(resource, policy, **_):
    if utils.resource_created(ctx, constants.RESOURCE_ID):
        return
    gcp_config = utils.get_gcp_config()
    policybinding = PolicyBinding(
        gcp_config,
        ctx.logger,
        resource,
        policy
    )
    utils.create(policybinding)
    ctx.instance.runtime_properties.update(policybinding.get())


@operation(resumable=True)
@utils.throw_cloudify_exceptions
def delete(resource, policy, **_):
    gcp_config = utils.get_gcp_config()
    policybinding = PolicyBinding(
        gcp_config,
        ctx.logger,
        resource,
        policy
    )
    policybinding.delete()
