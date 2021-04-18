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

from .. import gcp
from .. import utils
from .. import constants
from ..admin import CloudResourcesBase


class PolicyBinding(CloudResourcesBase):
    # https://cloud.google.com/resource-manager/reference/rest/v1/Policy
    # Example Gcloud Command:
    # gcloud iam service-accounts add-iam-policy-binding
    # [Service Account]
    # --member='user:[Service Account]'
    # --role=projects/[Project]/roles/[Role Name]

    def __init__(self, config, logger, service_accounts, policies):
        super(CloudResourcesBase, self).__init__(config, logger)
        self.resource = service_accounts
        self.new_policy = policies

    @gcp.check_response
    def get(self):
        return self.discovery.projects().getIamPolicy(
            resource=self.resource).execute()

    @gcp.check_response
    def create(self):
        # https://cloud.google.com/resource-manager/
        # reference/rest/v1/projects/setIamPolicy
        return self.discovery.projects().setIamPolicy(
            resource=self.resource,
            policy=self.add_new_policies_to_current_policy()).execute()

    @gcp.check_response
    def delete(self):
        # https://cloud.google.com/iam/docs/granting-changing-revoking-access
        return self.discovery.projects().setIamPolicy(
            resource=self.resource,
            policy=self.remove_new_policies_from_current_policy()).execute()

    def add_new_policies_to_current_policy(self):
        current_policy = deepcopy(self.get())
        # TODO: Actually devise how to add a policy to an existing policy.
        current_policy.update(self.new_policy)
        return current_policy

    def remove_new_policies_from_current_policy(self):
        current_policy = self.get()
        # TODO: Remove new policy
        return current_policy


@operation(resumable=True)
@utils.throw_cloudify_exceptions
def create(service_accounts, policies, **_):
    # TODO: Decide which parameters should be exposed.
    # TODO: Update Plugin YAML.
    if utils.resource_created(ctx, constants.RESOURCE_ID):
        return
    gcp_config = utils.get_gcp_config()
    policy = PolicyBinding(
        gcp_config,
        ctx.logger,
        service_accounts,
        policies
    )
    utils.create(policy)
    ctx.instance.runtime_properties.update(policy)


@operation(resumable=True)
@utils.throw_cloudify_exceptions
def delete(service_accounts, policies, **_):
    gcp_config = utils.get_gcp_config()
    policy = PolicyBinding(
        gcp_config,
        ctx.logger,
        service_accounts,
        policies
    )
    policy.delete()
