# #######
# Copyright (c) 2018 GigaSpaces Technologies Ltd. All rights reserved
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
from .. import constants
from .. import utils
from ..gcp import check_response
from ..pubsub import PubSubBase


class PullRequest(PubSubBase):
    def __init__(self,
                 config,
                 logger,
                 subscription,
                 return_immediately=False,
                 max_messages=0,
                 name='PullRequest',):
        """
        Create PullRequest object to pull message from topic subscription

        :param config: gcp auth file
        :param logger: logger object
        :param name: name of the subscription
        """
        super(PullRequest, self).__init__(
            config, logger, utils.get_gcp_resource_name(name),)

        self.name = name
        self.subscription = subscription
        self.return_immediately = return_immediately
        self.max_messages = max_messages

    @check_response
    def create(self):
        """
        Pull GCP Messages From Subscription Topic
        :return: REST response body contains the following:
            {
              "receivedMessages": [
                {
                  object(ReceivedMessage)
                }
              ],
            }
        """
        self.logger.info(
            "Pull Messages From Subscription {}".format(
                self.subscription_path))

        return self.discovery_pubsub.subscriptions().pull(
            subscription=self.subscription_path,
            body=self.to_dict()).execute()

    def to_dict(self):
        return {'returnImmediately': self.return_immediately,
                'maxMessages': self.max_messages}

    @property
    def subscription_path(self):
        return 'projects/{0}/subscriptions/{1}'.format(self.project,
                                                       self.subscription)


@operation
@utils.retry_on_failure('Retrying pulling subscription messages')
@utils.throw_cloudify_exceptions
def pull(subscription, return_immediately,
         max_messages, **kwargs):

    gcp_config = utils.get_gcp_config()
    pull_request = PullRequest(gcp_config, ctx.logger,
                               subscription,
                               return_immediately=return_immediately,
                               max_messages=max_messages)

    utils.set_resource_id_if_use_external(pull_request.subscription_path)
    # Handle pull messages response
    response = pull_request.create()
    ctx.logger.info('Pull received messages {}'.format(response))
    if response.get('receivedMessages')\
            and len(response['receivedMessages']) == max_messages:

        # Get the ack_ids so that we can use them to acknowledge the
        # message later on, so these ``ack_ids`` need to be available
        ack_ids = []
        for message in response['receivedMessages']:
            ack_ids.append(message['ackId'])

        ctx.instance.runtime_properties.update({'ack_ids': ack_ids})

    else:
        server_message = len(response['receivedMessages']) if \
            response.get('receivedMessages') else 0

        ctx.operation.retry('Only {0} messages'
                            ' have been pulled'.format(server_message),
                            constants.RETRY_DEFAULT_DELAY)
