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
from ..monitoring import MonitoringBase


class Group(MonitoringBase):
    def __init__(self,
                 config,
                 logger,
                 name,
                 display_name,
                 filter_criteria,
                 parent_name=None,
                 is_cluster=False,):
        """
        Create Monitoring Group object

        :param config: dictionary with project properties: path to auth file,
        project and zone
        :param logger: logger object that the class methods will be logging to
        """
        super(Group, self).__init__(config, logger, name)
        self.display_name = display_name
        self.parent_name = parent_name
        self.filter_criteria = filter_criteria
        self.is_cluster = is_cluster

    @check_response
    def create(self):
        return self.discovery_monitoring.groups().create(
            body=self.to_dict(),
            name=self.project_path).execute()

    @check_response
    def update(self):
        return self.discovery_monitoring.groups().update(
            body=self.to_dict(),
            name=self.name).execute()

    @check_response
    def delete(self):
        return self.discovery_monitoring.groups().delete(
            name=self.name).execute()

    @check_response
    def get(self):
        return self.discovery_monitoring.groups().get(name=self.name).execute()

    @property
    def project_path(self):
        return 'projects/{0}'.format(self.project)

    def to_dict(self):
        group_request = dict()
        group_request['displayName'] = self.display_name
        group_request['parentName'] = self.parent_name or ""
        group_request['filter'] = self.filter_criteria
        group_request['isCluster'] = self.is_cluster
        return group_request


@operation
@utils.throw_cloudify_exceptions
def create(name, display_name,
           parent_name, filter_criteria,
           is_cluster, **kwargs):

    name = utils.get_final_resource_name(name)
    gcp_config = utils.get_gcp_config()
    group = Group(gcp_config,
                  ctx.logger,
                  name=name,
                  display_name=display_name,
                  filter_criteria=filter_criteria,
                  parent_name=parent_name,
                  is_cluster=is_cluster,)

    response = utils.create(group)

    # Update the name of the group set by api
    group.name = response.get('name')
    ctx.logger.info('Monitoring group {0}'
                    ' created successfully {1}'.format(group.name, response))

    # Update the runtime properties by including the whole response
    ctx.instance.runtime_properties.update(group.get())


@operation
@utils.throw_cloudify_exceptions
def delete(**kwargs):
    gcp_config = utils.get_gcp_config()
    name = ctx.instance.runtime_properties.get('name')
    display_name = ctx.instance.runtime_properties.get('displayName')
    filter_criteria = ctx.instance.runtime_properties.get('filter')
    if all([name, display_name, filter_criteria]):
        group = Group(gcp_config,
                      ctx.logger,
                      name=name,
                      display_name=display_name,
                      filter_criteria=filter_criteria,)
        group.delete()
        ctx.logger.info('Monitoring group deleted successfully')
    else:
        raise NonRecoverableError(
            'Missing required parameters for delete group')


@operation
@utils.throw_cloudify_exceptions
def update(name, display_name,
           parent_name, filter_criteria,
           is_cluster, **kwargs):

    gcp_config = utils.get_gcp_config()
    group = Group(gcp_config,
                  ctx.logger,
                  name=name,
                  display_name=display_name,
                  filter_criteria=filter_criteria,
                  parent_name=parent_name,
                  is_cluster=is_cluster,)

    response = group.update()
    ctx.logger.info(
        'The response of updating monitoring group is {}'.format(response))
    ctx.instance.runtime_properties.update(group.get())
