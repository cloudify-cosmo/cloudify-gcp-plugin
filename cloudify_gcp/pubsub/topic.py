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


class Topic(PubSubBase):
    def __init__(self,
                 config,
                 logger,
                 name,
                 ):
        """
        Create Topic object

        :param config: gcp auth file
        :param logger: logger object
        :param name: name for the topic

        """
        super(Topic, self).__init__(config, logger,
                                    utils.get_gcp_resource_name(name),
                                    additional_settings=None,)
        self.name = name
        self._topic_path = self.topic_path

    @check_response
    def create(self):
        """
        Create GCP Topic.
        :return: REST response contains a newly created instance of Topic
        Resource  {"name": string,}
        """
        self.logger.info("Create Topic '{0}'".format(self.name))
        return self.discovery_pubsub.topics().create(
            name=self._topic_path, body={}).execute()

    @check_response
    def delete(self):
        """
        Delete GCP Topic.
        :return: REST response body will be empty
        """
        self.logger.info("Delete Topic '{0}'".format(self.name))
        return self.discovery_pubsub.topics().delete(
            topic=self._topic_path).execute()

    @check_response
    def get(self):
        return self.discovery_pubsub.topics().get(
            topic=self._topic_path).execute()

    @property
    def topic_path(self):
        return 'projects/{0}/topics/{1}'.format(self.project, self.name)


@operation
@utils.retry_on_failure('Retrying creating topic')
@utils.throw_cloudify_exceptions
def create(name, **kwargs):
    gcp_config = utils.get_gcp_config()
    if not name:
        name = ctx.node.id
    name = utils.get_final_resource_name(name)

    topic = Topic(gcp_config, ctx.logger, name, )

    resource = utils.create(topic)
    ctx.instance.runtime_properties.update(
        {'name': name, 'topic_path': resource.get('name')})


@operation
@utils.retry_on_failure('Retrying deleting topic')
@utils.throw_cloudify_exceptions
def delete(**kwargs):
    gcp_config = utils.get_gcp_config()
    name = ctx.instance.runtime_properties.get('name')
    if name:
        topic = Topic(gcp_config, ctx.logger, name)

        utils.delete_if_not_external(topic)

        if not utils.is_object_deleted(topic):
            ctx.operation.retry('Topic is not yet deleted. Retrying:',
                                constants.RETRY_DEFAULT_DELAY)
