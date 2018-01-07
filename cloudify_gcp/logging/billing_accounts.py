# #######
# Copyright (c) 2017 GigaSpaces Technologies Ltd. All rights reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
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
from cloudify.exceptions import NonRecoverableError

# Local imports
from .. import utils
from ..gcp import check_response
from . import LoggingBase


class BillingAccountsSinks(LoggingBase):
    def __init__(self,
                 config,
                 logger,
                 name,
                 destination,
                 filter_sink=None,
                 include_children=False,
                 unique_writer_identity=False):
        """
         Logging Base Class
        :param config: dictionary with project properties: path to auth file,
        project and zone
        :param logger: logger object that the class methods will be logging to
        """
        super(BillingAccountsSinks, self).__init__(config, logger, name,)
        self.destination = destination
        self.filter_sink = filter_sink
        self.include_children = include_children
        self.unique_writer_identity = unique_writer_identity

    @check_response
    def get(self):
        return self.discovery_monitoring.sinks().get(
            sinkName=self.sink_path,).execute()

    @check_response
    def create(self):
        return self.discovery_monitoring.sinks().create(
            parent=self.project_path,
            uniqueWriterIdentity=self.unique_writer_identity,
            body=self.to_dict(), ).execute()

    @check_response
    def update(self):
        return self.discovery_monitoring.sinks().update(
            sinkName=self.sink_path,
            updateMask='destination,filter,includeChildren',
            uniqueWriterIdentity=self.unique_writer_identity,
            body=self.to_dict(), ).execute()

    @check_response
    def delete(self):
        return self.discovery_monitoring.sinks().update(
            sinkName=self.project_path,
            body={}, ).execute()

    def to_dict(self):
        sink_request = dict()

        # Set the name of the sink
        sink_request['name'] = self.name

        # Set the destination of the log sink
        sink_request['destination'] = self.destination

        # Set the filter sink as part of the request if set
        if self.filter_sink:
            sink_request['filter'] = self.filter_sink

        if self.include_children:
            sink_request['includeChildren'] = self.include_children

        return sink_request

    @property
    def discovery_monitoring(self):
        return self.discovery.billingAccounts() if self.discovery else None

    @property
    def project_path(self):
        return 'projects/{0}'.format(self.project)

    @property
    def sink_path(self):
        return '{0}/sinks/{1}'.format(self.project_path, self.name)


@operation
@utils.throw_cloudify_exceptions
def create(name, destination,
           filter_sink, include_children,
           unique_writer_identity, **kwargs):

    name = utils.get_final_resource_name(name)
    gcp_config = utils.get_gcp_config()
    billing_sink_account = \
        BillingAccountsSinks(gcp_config, ctx.logger,
                             name=name, destination=destination,
                             filter_sink=filter_sink,
                             include_children=include_children,
                             unique_writer_identity=unique_writer_identity,)

    response = utils.create(billing_sink_account)
    ctx.logger.info(
        'Billing accounts sink created successfully {}'.format(response))
    ctx.instance.runtime_properties.update(response)


@operation
@utils.throw_cloudify_exceptions
def delete(**kwargs):
    gcp_config = utils.get_gcp_config()
    name = ctx.instance.runtime_properties.get('name')
    destination = ctx.instance.runtime_properties.get('destination')
    if all([name, destination]):
        billing_sink_account = BillingAccountsSinks(gcp_config,
                                                    ctx.logger,
                                                    name=name,
                                                    destination=destination,)
        billing_sink_account.delete()
        ctx.logger.info('Billing accounts sink successfully')
    else:
        raise NonRecoverableError(
            'Missing required parameters for delete group')


@operation
@utils.throw_cloudify_exceptions
def update(name, destination,
           filter_sink, include_children,
           unique_writer_identity, **kwargs):

    name = utils.get_final_resource_name(name)
    gcp_config = utils.get_gcp_config()
    billing_sink_account = \
        BillingAccountsSinks(gcp_config, ctx.logger,
                             name=name, destination=destination,
                             filter_sink=filter_sink,
                             include_children=include_children,
                             unique_writer_identity=unique_writer_identity,)

    response = billing_sink_account.update()
    ctx.logger.info(
        'Billing accounts sink updated successfully {}'.format(response))
    ctx.instance.runtime_properties.update(response)