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

# Standard library imports
from __future__ import unicode_literals

# Third-party imports
from cloudify import ctx
from cloudify.decorators import operation

# Local imports
from .. import utils
from ..gcp import check_response
from ..pubsub import PubSubBase


class SubscriptionPolicy(PubSubBase):
    def __init__(self,
                 config,
                 logger,
                 subscription,
                 policy,
                 name='PubSubPolicy',):
        """
        Create Pub/Sub Policy

        :param config: gcp auth file
        :param logger: logger object
        :param name: name for the topic policy resource
        :param policy: policy object that contains the following :
            - bindings: Associates a list of members to a role
            - role: Role that is assigned to members.
            - members: Specifies the identities requesting access for
             a Cloud Platform resource
             More info can be found on google api docs
             https://cloud.google.com/pubsub/docs/reference/rest/v1/Policy

        :param topic: name of the topic need to set policy for

        """
        super(SubscriptionPolicy, self).__init__(
            config,
            logger,
            utils.get_gcp_resource_name(name),)

        self.name = name
        self.policy = policy
        self.subscription = subscription

    @check_response
    def create(self):
        """
        Create GCP Pub/Sub Policy.
        :return: REST response contains a newly created instance of policy
        """
        self.logger.info("Create Topic Policy '{0}'".format(self.name))
        return self.discovery_pubsub.subscriptions().setIamPolicy(
            resource=self.subscription_path, body=self.to_dict()).execute()

    @check_response
    def delete(self):
        pass

    def to_dict(self):
        return {'policy': self.policy}

    @property
    def subscription_path(self):
        return 'projects/{0}/subscriptions/{1}'.format(self.project,
                                                       self.subscription)


@operation
@utils.retry_on_failure('Retrying setting iam subscription policy')
@utils.throw_cloudify_exceptions
def set_policy(subscription, policy, **kwargs):

    gcp_config = utils.get_gcp_config()
    topic_policy = SubscriptionPolicy(gcp_config, ctx.logger,
                                      subscription, policy,)

    utils.set_resource_id_if_use_external(topic_policy.subscription_path)
    resource = utils.create(topic_policy)
    ctx.instance.runtime_properties.update(resource)
    ctx.logger.info('Policy {0} updated successfully '.format(resource))
