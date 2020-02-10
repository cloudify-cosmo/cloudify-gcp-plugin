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
from .. import constants
from .. import utils
from ..gcp import check_response
from ..pubsub import PubSubBase


class Subscription(PubSubBase):
    def __init__(self,
                 config,
                 logger,
                 name,
                 topic,
                 push_config=None,
                 ack_deadline_seconds=0,):
        """
        Create Subscription object

        :param config: gcp auth file
        :param logger: logger object
        :param name: name of the subscription
        :param topic: name of the topic to subscribe for
        :param push_config: The name of the topic from which this subscription
         is receiving messages
        :param ack_deadline_seconds: This value is the maximum time after a
         subscriber receives a message before the subscriber should
         acknowledge the message

        """
        super(Subscription, self).__init__(
            config, logger, utils.get_gcp_resource_name(name),)
        self.name = name
        self.topic = topic
        self.push_config = push_config
        self.ack_deadline_seconds = ack_deadline_seconds

    @check_response
    def create(self):
        """
        Create GCP Subscription.
        :return: REST response contains a newly created instance
         of Subscription
          {
            "name": string,
            "topic": string,
            "pushConfig": {
                object(PushConfig)
            },
          "ackDeadlineSeconds": number,
          }

        """
        self.logger.info("Create Subscription '{0}'".format(self.name))
        return self.discovery_pubsub.subscriptions().create(
            name=self.subscription_path, body=self.to_dict()).execute()

    def to_dict(self):
        body = dict()

        # Topic path
        body['topic'] = self.topic_path

        # only set the ``ackDeadlineSeconds`` if it is already set by the user
        if self.ack_deadline_seconds:
            body['ackDeadlineSeconds'] = self.ack_deadline_seconds

        # If this ``pushConfig`` empty then it is a pull delivery
        body['pushConfig'] = {}

        # If it is a push delivery then we need to check the following data
        if self.push_config:

            # Get the ``push_endpoint`` data
            if self.push_config.get('push_endpoint'):
                body['pushConfig']['pushEndpoint'] =\
                    self.push_config['push_endpoint']

            # Get the ``attributes`` data
            if self.push_config.get('attributes'):
                body['pushConfig']['attributes'] =\
                    self.push_config['attributes']

        return body

    @check_response
    def delete(self):
        """
        Delete GCP Subscription.
        :return: REST response body will be empty
        """
        self.logger.info("Delete Subscription '{0}'".format(self.name))
        return self.discovery_pubsub.subscriptions().delete(
            subscription=self.subscription_path).execute()

    @check_response
    def get(self):
        return self.discovery_pubsub.subscriptions().get(
            subscription=self.subscription_path).execute()

    @property
    def subscription_path(self):
        return 'projects/{0}/subscriptions/{1}'.format(self.project, self.name)

    @property
    def topic_path(self):
        return 'projects/{0}/topics/{1}'.format(self.project, self.topic)


@operation
@utils.retry_on_failure('Retrying creating subscription')
@utils.throw_cloudify_exceptions
def create(topic, name, push_config=None,
           ack_deadline_seconds=0, **kwargs):

    gcp_config = utils.get_gcp_config()
    if not name:
        name = ctx.node.id
    name = utils.get_final_resource_name(name)
    subscription = Subscription(gcp_config, ctx.logger,
                                name, topic,
                                push_config, ack_deadline_seconds)

    resource = utils.create(subscription)
    ctx.instance.runtime_properties.update(
        {'name_path': resource.get('name'),
         'topic_path': resource.get('topic'),
         'push_config': resource.get('pushConfig'),
         'ack_deadline_seconds': resource.get('ackDeadlineSeconds')
         }
    )
    ctx.instance.runtime_properties['topic'] = topic
    ctx.instance.runtime_properties['name'] = name


@operation
@utils.retry_on_failure('Retrying deleting subscription')
@utils.throw_cloudify_exceptions
def delete(**kwargs):
    gcp_config = utils.get_gcp_config()
    name = ctx.instance.runtime_properties.get('name')
    topic = ctx.instance.runtime_properties.get('topic')
    if name:
        subscription = Subscription(gcp_config, ctx.logger,
                                    name, topic)

        utils.delete_if_not_external(subscription)

        if not utils.is_object_deleted(subscription):
            ctx.operation.retry('subscription is not yet deleted. Retrying:',
                                constants.RETRY_DEFAULT_DELAY)
