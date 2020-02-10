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
import base64

# Third-party imports
from cloudify import ctx
from cloudify.decorators import operation

# Local imports
from .. import utils
from ..gcp import check_response
from ..pubsub import PubSubBase


class TopicMessage(PubSubBase):
    def __init__(self,
                 config,
                 logger,
                 topic,
                 messages,
                 name='TopicMessage',
                 ):
        """
        Create Topic Message object

        :param config: gcp auth file
        :param logger: logger object
        :param name: name for the topic message resource
        :param messages: list of PubsubMessage object the contains the
        following :
            - data: The message payload.A base64-encoded string.
            - attributes: Optional attributes for this message.
             An object containing a list of "key": value pairs.
              Example: { "name": "wrench", "mass": "1.3kg", "count": "3" }.

        :param topic: name of the topic need to publish message for

        """
        super(TopicMessage, self).__init__(
            config,
            logger,
            utils.get_gcp_resource_name(name),)

        self.name = name
        self.messages = messages
        self.topic = topic

    @check_response
    def create(self):
        """
        Create GCP Topic Message.
        :return: REST response contains a newly created list of generated
        message ids
        """
        self.logger.info("Create Topic Message '{0}'".format(self.name))
        return self.discovery_pubsub.topics().publish(
            topic=self.topic_path, body=self.to_dict()).execute()

    @check_response
    def delete(self):
        pass

    def to_dict(self):
        for index, message in enumerate(self.messages):
            if message.get('data'):
                message['data'] = base64.b64encode(message['data'])

        return {'messages': self.messages}

    @property
    def topic_path(self):
        return 'projects/{0}/topics/{1}'.format(self.project, self.topic)


@operation(resumable=True)
@utils.retry_on_failure('Retrying publishing topic message')
@utils.throw_cloudify_exceptions
def publish(topic, messages, **kwargs):
    gcp_config = utils.get_gcp_config()
    topic_message = TopicMessage(gcp_config, ctx.logger, topic, messages, )

    utils.set_resource_id_if_use_external(topic_message.topic_path)
    resource = utils.create(topic_message)
    ctx.instance.runtime_properties.update(resource)
    ctx.logger.info('Messages genearted successfully {0}'.format(resource))
