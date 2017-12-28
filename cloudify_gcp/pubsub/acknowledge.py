# #######
# Copyright (c) 2017 GigaSpaces Technologies Ltd. All rights reserved
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

# Standard library imports
from __future__ import unicode_literals

# Third-party imports
from cloudify import ctx
from cloudify.decorators import operation

# Local imports
from .. import utils
from ..gcp import check_response
from ..pubsub import PubSubBase


class Acknowledge(PubSubBase):
    def __init__(self,
                 config,
                 logger,
                 subscription,
                 ack_ids,
                 name='Acknowledge',
                 ):
        """
        Create Acknowledge object

        :param config: gcp auth file
        :param logger: logger object
        :param subscription: The subscription whose message
         is being acknowledged
        :param ack_ids: list of The acknowledgment ID for the
         messages being acknowledged.
        :param name: name for the acknowledge resource
        """
        super(Acknowledge, self).__init__(
            config,
            logger,
            utils.get_gcp_resource_name(name),)

        self.name = name
        self.subscription = subscription
        self.ack_ids = ack_ids

    @check_response
    def create(self):
        """
        Acknowledge GCP Messages.
        :return: REST response body will be empty
        """
        self.logger.info("Acknowledge Messages '{0}'".format(self.ack_ids))
        return self.discovery_pubsub.subscriptions().acknowledge(
            subscription=self.subscription_path, body=self.to_dict()).execute()

    @check_response
    def delete(self):
        pass

    def to_dict(self):
        return {'ackIds': self.ack_ids}

    @property
    def subscription_path(self):
        return 'projects/{0}/subscriptions/{1}'.format(self.project,
                                                       self.subscription)


@operation
@utils.retry_on_failure('Retrying acknowledge message')
@utils.throw_cloudify_exceptions
def create(subscription, ack_ids, **kwargs):
    gcp_config = utils.get_gcp_config()
    ack = Acknowledge(gcp_config, ctx.logger, subscription, ack_ids,)
    utils.create(ack)
    ctx.instance.runtime_properties.update(
        {'sub': subscription, 'ack_ids': ack_ids})
