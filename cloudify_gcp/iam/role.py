# #######
# Copyright (c) 2017-2020 Cloudify Platform Ltd. All rights reserved
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

import re

# Third-party imports
from cloudify import ctx
from cloudify.decorators import operation
from cloudify.exceptions import OperationRetry

# Local imports
from cloudify_gcp import utils
from cloudify_gcp import constants
from cloudify_gcp.iam import IAMBase
from cloudify_gcp.gcp import check_response

PATTERN = "^projects/[^/]+/roles/[^/]+$"
DELETING_MESSAGE = 'Waiting for role to be deleted. ' \
                   'Role deleted value is {deleted}.'


class Role(IAMBase):
    def __init__(self,
                 config,
                 logger,
                 name,
                 title=None,
                 description=None,
                 permissions=None,
                 stage=None,
                 additional_settings=None):
        """
                Create GCP IAM Role object

        :param config:
        :param logger:
        :param name:
        :param title:
        :param description:
        :param permissions:
        :param stage:
        :param additional_settings:
        """

        super(Role, self).__init__(config,
                                   logger,
                                   name,
                                   additional_settings,)
        self.title = title or self.name
        self.description = description
        self.permissions = permissions
        self.stage = stage
        self.parent = 'projects/{project}'.format(project=self.project)
        self.name_for_retrieval = '{parent}/roles/{name}'.format(
            parent=self.parent, name=self.name)

    @check_response
    def create(self):
        return self.discovery.projects().roles().create(
            parent=self.parent, body=self.to_dict()).execute()

    @check_response
    def delete(self):
        return self.discovery.projects().roles().delete(
            name=self.name_for_retrieval).execute()

    @check_response
    def list(self):
        response = self.discovery.projects().roles().list(
            parent=self.parent).execute()
        return response['roles']

    @check_response
    def get(self):
        return self.discovery.projects().roles().get(
            name=self.name_for_retrieval).execute()

    def to_dict(self):
        return {
            'roleId': self.name,
            'role': {
                'title': self.title,
                'description': self.description,
                'includedPermissions': self.permissions,
                'stage': self.stage
            }
        }


@operation(resumable=True)
@utils.throw_cloudify_exceptions
def create(name, title, description, permissions, stage, **_):
    if utils.resource_created(ctx, constants.NAME):
        return

    name = utils.get_final_resource_name(name)
    gcp_config = utils.get_gcp_config()
    role = Role(gcp_config,
                ctx.logger,
                name=name,
                title=title,
                description=description,
                permissions=permissions,
                stage=stage)

    ctx.instance.runtime_properties[constants.NAME] = name
    utils.create(role)
    ctx.instance.runtime_properties.update(role.get())


@operation(resumable=True)
@utils.throw_cloudify_exceptions
def delete(**_):
    gcp_config = utils.get_gcp_config()
    name = ctx.instance.runtime_properties.get(constants.NAME)
    if name:
        if re.match(PATTERN, name):
            name = name.split('/roles/')[-1]
        role = Role(gcp_config,
                    ctx.logger,
                    name=name)
        role_dict = role.get()
        deleted = role_dict.get('deleted')
        if not deleted:
            role.delete()
            raise OperationRetry(DELETING_MESSAGE.format(deleted=deleted))
