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
from cloudify.decorators import operation
from cloudify import ctx

from oauth2client.client import GoogleCredentials
from oauth2client import GOOGLE_TOKEN_URI

from .. import constants
from .. import utils
from .. import gcp


class Project(gcp.GoogleCloudApi):

    def __init__(self, config, logger, project_id=None, name=None,
                 scope=constants.COMPUTE_SCOPE,
                 discovery=constants.CLOUDRESOURCES_DISCOVERY,
                 api_version=constants.API_V1):
        super(Project, self).__init__(config, logger, scope, discovery,
                                      api_version)

        self.project_id = utils.get_gcp_resource_name(project_id)
        self.name = name if name else self.project_id

    def get_credentials(self, scope):
        # check
        # run: gcloud beta auth application-default login
        # look to ~/.config/gcloud/application_default_credentials.json
        credentials = GoogleCredentials(
            access_token=None,
            client_id=self.auth['client_id'],
            client_secret=self.auth['client_secret'],
            refresh_token=self.auth['refresh_token'],
            token_expiry=None,
            token_uri=GOOGLE_TOKEN_URI,
            user_agent='Python client library'
        )
        self.logger.debug('Credentials: {}'.format(
            repr(credentials.to_json())
        ))
        return credentials

    @gcp.check_response
    def get(self):
        """
        Get GCP project details.

        :return: REST response with operation responsible for the project
        details retrieval
        """
        self.logger.info('Get instance {0} details'.format(self.name))

        return self.discovery.projects().get(
            projectId=self.project_id).execute()

    @gcp.check_response
    def create(self):
        project_body = {
            constants.NAME: utils.get_gcp_resource_name(
                ctx.node.properties[constants.NAME]),
            'projectId': self.project_id
        }
        self.logger.info('Project info: {}'.format(repr(project_body)))
        return self.discovery.projects().create(
            body=project_body).execute()

    @gcp.check_response
    def delete(self):
        return self.discovery.projects().delete(
            projectId=self.project_id).execute()


@operation(resumable=True)
@utils.throw_cloudify_exceptions
def create(**kwargs):
    if utils.resorce_created(ctx, constants.RESOURCE_ID):
        return

    gcp_config = utils.get_gcp_config()

    project = Project(
        gcp_config,
        ctx.logger,
        ctx.node.properties['id'],
        ctx.node.properties[constants.NAME]
    )
    utils.create(project)

    ctx.instance.runtime_properties[constants.RESOURCE_ID] = project.project_id


@operation(resumable=True)
@utils.throw_cloudify_exceptions
def delete(**kwargs):
    gcp_config = utils.get_gcp_config()
    props = ctx.instance.runtime_properties

    if props.get(constants.RESOURCE_ID):
        project = Project(
            gcp_config,
            ctx.logger,
            props[constants.RESOURCE_ID]
        )

        utils.delete_if_not_external(project)
        ctx.instance.runtime_properties[constants.RESOURCE_ID] = None
