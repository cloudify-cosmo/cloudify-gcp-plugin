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


class LoggingMixin(object):

    @property
    def discovery_monitoring(self):
        return self.discovery.billingAccounts() if self.discovery else None

    @property
    def project_path(self):
        return 'projects/{0}'.format(self.project)

    @property
    def billing_account_path(self):
        return 'billingAccounts/{0}'.format(self.billing_account_id)

    @property
    def operation_path(self):
        return '{0}/{1}/{2}'.format(self.billing_account_path,
                                    self.billing_account_operation, self.name)


class LogSink(LoggingMixin, LoggingBase):
    billing_account_operation = 'sinks'

    def __init__(self,
                 config,
                 logger,
                 name,
                 billing_account_id,
                 destination,
                 filter_sink=None,
                 include_children=False,
                 unique_writer_identity=False,
                 is_update=False):
        """
         Logging Base Class
        :param config: dictionary with project properties: path to auth file,
        project and zone

        :param logger: logger object that the class methods will be logging to

        :param name: The client-assigned sink identifier,
         unique within the project

        :param billing_account_id: Billing account ID associates
         with gcp account

        :param destination: The export destination

        :param filter_sink: The only exported log entries are those that
         are in the resource owning the sink and that match the filter

        :param include_children: Optional This field applies only to sinks
        owned by organizations and folders. If the field is false, the default,
        only the logs owned by the sink's parent resource are available
        for export. If the field is true, then logs from all the projects,
        folders, and billing accounts contained in the sink's parent
        resource are also available for export. Whether a particular log
        entry from the children is exported depends on the sink's filter
        expression. For example, if this field is true, then the filter
        resource.type=gce_instance would export all Compute Engine VM
        instance log entries from all projects in the sink's parent

        :param unique_writer_identity:Optional.
          Determines the kind of IAM identity returned as writerIdentity
          in the new sink. If this value is omitted or set to false,
          and if the sink's parent is a project, then the value returned as
          writerIdentity is the same group or service account used by
          Stackdriver Logging before the addition of writer identities to
          this API.
          The sink's destination must be in the same project as the sink
          itself. If this field is set to true, or if the sink is owned by
          a non-project resource such as an organization,
          then the value of writerIdentity will be a unique service account
          used only for exports from the new sink

        :param is_update: is a flag to check whether the action is
        create or update for the log sink

        """
        super(LogSink, self).__init__(config, logger, name, )
        self.billing_account_id = billing_account_id
        self.destination = destination
        self.filter_sink = filter_sink
        self.include_children = include_children
        self.unique_writer_identity = unique_writer_identity
        self.is_update = is_update

    @check_response
    def get(self):
        return self.discovery_monitoring.sinks().get(
            sinkName=self.operation_path,).execute()

    @check_response
    def create(self):
        return self.discovery_monitoring.sinks().create(
            parent=self.billing_account_path,
            uniqueWriterIdentity=self.unique_writer_identity,
            body=self.to_dict(), ).execute()

    @check_response
    def update(self):
        return self.discovery_monitoring.sinks().update(
            sinkName=self.operation_path,
            updateMask='destination,filter,includeChildren',
            uniqueWriterIdentity=self.unique_writer_identity,
            body=self.to_dict(), ).execute()

    @check_response
    def delete(self):
        return self.discovery_monitoring.sinks().delete(
            sinkName=self.project_path,
            body={}, ).execute()

    def to_dict(self):
        sink_request = dict()

        # Set the name of the sink
        # Only include the name on the request if the action is create
        # API does not allow the name to be updated when the action is update
        if not self.is_update:
            sink_request['name'] = self.name

        # Set the destination of the log sink
        sink_request['destination'] = self.destination

        # Set the filter sink as part of the request if set
        if self.filter_sink:
            sink_request['filter'] = self.filter_sink

        if self.include_children:
            sink_request['includeChildren'] = self.include_children

        return sink_request


class LogExclusion(LoggingMixin, LoggingBase):
    billing_account_operation = 'exclusions'

    def __init__(self,
                 config,
                 logger,
                 name,
                 billing_account_id,
                 filter_exclusions,
                 description=None,
                 disabled=False,
                 is_update=False):
        """
         Logging Base Class
        :param config: dictionary with project properties: path to auth file,
        project and zone

        :param logger: logger object that the class methods will be logging to

        :param name: Required. A client-assigned identifier,
        such as "load-balancer-exclusion". Identifiers are limited to 100
        characters and can include only letters, digits, underscores,
        hyphens, and periods.

        :param billing_account_id: Billing account ID associates with gcp
        account

        :param filter_exclusions: Required. An advanced logs filter
        that matches the log entries to be excluded. By using
        the sample function, you can exclude less than 100%
        of the matching log entries

        :param description: Optional. A description of this exclusion.

        :param disabled: Optional. If set to True, then this exclusion
        is disabled and it does not exclude any log entries.
        You can use exclusions.patch to change the value of this field

        :param is_update: is a flag to check whether the action is
        create or update for the log exclusion

        """
        super(LogExclusion, self).__init__(config, logger, name, )
        self.billing_account_id = billing_account_id
        self.filter_exclusions = filter_exclusions
        self.description = description
        self.disabled = disabled
        self.is_update = is_update

    @check_response
    def get(self):
        return self.discovery_monitoring.exclusions().get(
            name=self.operation_path,).execute()

    @check_response
    def create(self):
        return self.discovery_monitoring.exclusions().create(
            parent=self.billing_account_path,
            body=self.to_dict(), ).execute()

    @check_response
    def update(self):
        return self.discovery_monitoring.exclusions().patch(
            name=self.operation_path,
            updateMask='filter,description',
            body=self.to_dict(), ).execute()

    @check_response
    def delete(self):
        return self.discovery_monitoring.exclusions().delete(
            name=self.operation_path,
            body={}, ).execute()

    def to_dict(self):
        exclusion_request = dict()

        # Set the name of the exclusion
        exclusion_request['name'] = self.name

        # Set the destination of the log exclusion
        exclusion_request['filter'] = self.filter_exclusions

        # Set the description for log exclusion as part of the request if
        # set and if the action is only create
        if self.description and not self.is_update:
            exclusion_request['description'] = self.description

        # Set the disabled for log exclusion as part of the request if set
        # and if the action is only create
        if self.disabled and not self.is_update:
            exclusion_request['disabled'] = self.disabled

        return exclusion_request


@operation
@utils.throw_cloudify_exceptions
def create_log_sink(name, billing_account_id, destination,
                    filter_sink, include_children,
                    unique_writer_identity, **kwargs):

    name = utils.get_final_resource_name(name)
    gcp_config = utils.get_gcp_config()
    billing_sink_account = \
        LogSink(gcp_config, ctx.logger,
                name=name,
                billing_account_id=billing_account_id,
                destination=destination,
                filter_sink=filter_sink,
                include_children=include_children,
                unique_writer_identity=unique_writer_identity, )

    response = utils.create(billing_sink_account)
    ctx.logger.info(
        'Billing accounts sink created successfully {}'.format(response))
    ctx.instance.runtime_properties.update(response)
    ctx.instance.runtime_properties['billing_account_id'] = billing_account_id


@operation
@utils.throw_cloudify_exceptions
def delete_log_sink(**kwargs):
    gcp_config = utils.get_gcp_config()
    name = ctx.instance.runtime_properties.get('name')
    destination = ctx.instance.runtime_properties.get('destination')
    billing_account_id =\
        ctx.instance.runtime_properties.get('billing_account_id')

    # All required params must be passed in order to delete the sink log
    # resource
    if all([name, destination, billing_account_id]):
        billing_sink_account =\
            LogSink(gcp_config, ctx.logger, name=name,
                    billing_account_id=billing_account_id,
                    destination=destination, )
        billing_sink_account.delete()
        ctx.logger.info('Billing accounts sink deleted successfully')
    else:
        raise NonRecoverableError('Not all required parameters provided to '
                                  'delete billing accounts sink')


@operation
@utils.throw_cloudify_exceptions
def update_log_sink(name, billing_account_id,  destination,
                    filter_sink, include_children,
                    unique_writer_identity, **kwargs):

    name = utils.get_final_resource_name(name)
    gcp_config = utils.get_gcp_config()
    billing_sink_account = \
        LogSink(gcp_config, ctx.logger,
                name=name, billing_account_id=billing_account_id,
                destination=destination,
                filter_sink=filter_sink,
                include_children=include_children,
                unique_writer_identity=unique_writer_identity,
                is_update=True,)

    response = billing_sink_account.update()
    ctx.logger.info(
        'Billing accounts sink updated successfully {}'.format(response))
    ctx.instance.runtime_properties.update(response)


@operation
@utils.throw_cloudify_exceptions
def create_log_exclusion(name, billing_account_id,
                         filter_exclusions, description, disabled, **kwargs):

    name = utils.get_final_resource_name(name)
    gcp_config = utils.get_gcp_config()
    exclusion_log = LogExclusion(gcp_config, ctx.logger,
                                 name=name,
                                 billing_account_id=billing_account_id,
                                 filter_exclusions=filter_exclusions,
                                 description=description,
                                 disabled=disabled,)

    response = utils.create(exclusion_log)
    ctx.logger.info('Billing accounts exclusion'
                    ' log created successfully {}'.format(response))
    ctx.instance.runtime_properties.update(response)
    ctx.instance.runtime_properties['billing_account_id'] = billing_account_id


@operation
@utils.throw_cloudify_exceptions
def delete_log_exclusion(**kwargs):
    gcp_config = utils.get_gcp_config()
    name = ctx.instance.runtime_properties.get('name')
    filter_exclusions =\
        ctx.instance.runtime_properties.get('filter_exclusions')
    billing_account_id =\
        ctx.instance.runtime_properties.get('billing_account_id')

    # All required params must be passed in order to delete the exclusion log
    if all([name, filter_exclusions, billing_account_id]):
        exclusion_log = LogExclusion(gcp_config, ctx.logger,
                                     name=name,
                                     billing_account_id=billing_account_id,
                                     filter_exclusions=filter_exclusions,)
        exclusion_log.delete()
        ctx.logger.info('Billing accounts exclusion log deleted successfully')
    else:
        raise NonRecoverableError('Not all required parameters provided to '
                                  'delete billing accounts exclusion log')


@operation
@utils.throw_cloudify_exceptions
def update_log_exclusion(name, billing_account_id, filter_exclusions,
                         description, disabled, **kwargs):

    name = utils.get_final_resource_name(name)
    gcp_config = utils.get_gcp_config()
    exclusion_log = LogExclusion(gcp_config, ctx.logger,
                                 name=name,
                                 billing_account_id=billing_account_id,
                                 filter_exclusions=filter_exclusions,
                                 description=description,
                                 disabled=disabled,
                                 is_update=True)

    response = exclusion_log.update()
    ctx.logger.info('Billing accounts exclusion'
                    ' log updated successfully {}'.format(response))
    ctx.instance.runtime_properties.update(response)
