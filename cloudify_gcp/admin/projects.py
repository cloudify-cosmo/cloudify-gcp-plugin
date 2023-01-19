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
from cloudify.exceptions import OperationRetry

from .. import gcp
from .. import utils
from .. import constants
from . import CloudResourcesBase


class Project(CloudResourcesBase):

    def __init__(self,
                 config,
                 logger,
                 name=None,
                 project_id=None,
                 parent=None):

        super(Project, self).__init__(config, logger)

        self.project_id = project_id if project_id else name
        self.name = name if name else project_id
        self.parent = parent

    @property
    def project_body(self):
        project_body = {
            'name': self.name,
            'projectId': self.project_id,
            'parent': self.parent
        }
        self.logger.debug('Project info: {}'.format(repr(project_body)))
        return project_body

    def get(self):
        """
        Get GCP project details.

        :return: REST response with operation responsible for the project
        details retrieval
        """
        self.logger.info('Get instance {0} details'.format(self.name))
        try:
            return self.discovery.projects().get(
                projectId=self.project_id).execute()
        except Exception as e:
            self.logger.debug(e)

    @gcp.check_response
    def create(self):
        return self.discovery.projects().create(
            body=self.project_body).execute()

    @gcp.check_response
    def delete(self):
        return self.discovery.projects().delete(
            projectId=self.project_id).execute()


@operation(resumable=True)
@utils.throw_cloudify_exceptions
def create(**_):

    if utils.resource_created(ctx, constants.RESOURCE_ID):
        return

    gcp_config = utils.get_gcp_config()
    project = Project(
        config=gcp_config,
        logger=ctx.logger,
        name=ctx.node.properties[constants.NAME],
        project_id=ctx.node.properties.get('project_id', None),
        parent=ctx.node.properties.get('parent', None)
    )

    resource_exists = project.get()
    if not resource_exists:
        utils.create(project)
    elif resource_exists.get('lifecycleStatus') == 'ACTIVE':
        return
    raise OperationRetry('The project state is not ACTIVE yet.')


# def get_info_form_project(project):
#     try:
#         return project.get()
#     except Exception as e:
#         raise OperationRetry("The project creation is not ready. {}".
#                              format(str(e)))


@operation(resumable=True)
@utils.throw_cloudify_exceptions
def delete(**_):
    gcp_config = utils.get_gcp_config()
    props = ctx.instance.runtime_properties

    if props.get(constants.RESOURCE_ID):
        project = Project(
            config=gcp_config,
            logger=ctx.logger,
            project_id=props[constants.RESOURCE_ID]
        )
        resource_exists = project.get()
        if resource_exists.get('lifecycleState') != 'ACTIVE':
            ctx.logger.info('The lifecycleState is not active, '
                            'you must delete the project manually.'
                            '{}'.format(resource_exists.get('lifecycleState')))
        utils.delete_if_not_external(project)
        ctx.instance.runtime_properties[constants.RESOURCE_ID] = None
