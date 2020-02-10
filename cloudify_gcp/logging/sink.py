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
from cloudify import ctx
from cloudify.decorators import operation
from cloudify_gcp.gcp import check_response
from cloudify.exceptions import NonRecoverableError

from .. import utils
from ..logging import BillingAccountBase


class LoggingSink(BillingAccountBase):
    def __init__(self, config, logger, sink_type, parent=None, log_sink=None,
                 name=None, update_mask=None, unique_writer_identity=False):
        super(LoggingSink, self).__init__(config, logger, name or parent)
        self.parent = parent
        self.unique_writer_identity = unique_writer_identity
        self.log_sink = log_sink
        self.name = name
        self.update_mask = update_mask

        if sink_type == 'BillingAccount':
            self.sink_discovery = self.discovery.billingAccounts().sinks()
        elif sink_type == 'Folder':
            self.sink_discovery = self.discovery.folders().sinks()
        elif sink_type == 'Organization':
            self.sink_discovery = self.discovery.organizations().sinks()
        elif sink_type == 'Project':
            self.sink_discovery = self.discovery.projects().sinks()
        else:
            raise NonRecoverableError('Invalid sink type of {}'.format(
                sink_type))

    @check_response
    def create(self):
        return self.sink_discovery.create(
            uniqueWriterIdentity=self.unique_writer_identity,
            parent=self.parent,
            body=self.log_sink).execute()

    @check_response
    def delete(self):
        return self.sink_discovery.delete(
            sinkName=self.name).execute()

    @check_response
    def update(self):
        return self.sink_discovery.patch(
            body=self.log_sink, sinkName=self.name,
            uniqueWriterIdentity=self.unique_writer_identity,
            updateMask=self.update_mask).execute()


@operation(resumable=True)
@utils.throw_cloudify_exceptions
def create(ctx, parent, log_sink, sink_type, **kwargs):
    gcp_config = utils.get_gcp_config()
    billing_sink = LoggingSink(
        gcp_config, ctx.logger, sink_type, parent, log_sink, **kwargs)
    resource = utils.create(billing_sink)
    ctx.instance.runtime_properties['name'] = '{}/sinks/{}'.format(
        parent, resource['name'])


@operation(resumable=True)
@utils.retry_on_failure('Retrying deleting billing sink')
@utils.throw_cloudify_exceptions
def delete(sink_type, **kwargs):
    gcp_config = utils.get_gcp_config()
    billing_sink = LoggingSink(
        gcp_config, ctx.logger, sink_type,
        name=ctx.instance.runtime_properties['name'])

    utils.delete_if_not_external(billing_sink)


@operation(resumable=True)
@utils.throw_cloudify_exceptions
def update(parent, log_sink, sink_type, **kwargs):
    gcp_config = utils.get_gcp_config()
    current_resource_name = ctx.instance.runtime_properties['name']
    billing_sink = LoggingSink(
        gcp_config, ctx.logger, sink_type, parent, log_sink,
        name=current_resource_name, **kwargs)
    billing_sink.update()
