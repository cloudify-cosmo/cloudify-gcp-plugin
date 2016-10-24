# #######
# Copyright (c) 2014 GigaSpaces Technologies Ltd. All rights reserved
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
from cloudify import ctx
from cloudify.decorators import operation

from cloudify_gcp.gcp import GoogleCloudPlatform
from cloudify_gcp.gcp import check_response
from .. import constants
from .. import utils
from cloudify_gcp.storage import Object


class Image(GoogleCloudPlatform):
    def __init__(self,
                 config,
                 logger,
                 name,
                 url=None,
                 id=None):
        """
        Create Image object

        :param config:
        :param logger:
        :param url: image url in storage to be uploaded
        :param id: image_id
        """
        super(Image, self).__init__(config, logger, name,
                                    scope=[constants.COMPUTE_SCOPE,
                                           constants.STORAGE_SCOPE_RW])
        self.url = url
        self.id = id
        self.config = config

    @check_response
    def create(self):
        # upload tar.gz to a bucket
        # check if this bucket exists, create if not
        # bucket will be named by project name
        # insert image from tar.gz to the projects

        return self.discovery.images().insert(project=self.project,
                                              body=self.to_dict()).execute()

    def upload_and_create(self, file_path):
        obj = Object(self.config, self.logger, '{0}.tar.gz'.format(self.name))
        self.url = obj.upload_to_bucket(path=file_path)
        self.create()

    @check_response
    def get(self):
        return self.discovery.images().get(project=self.project,
                                           image=self.name).execute()

    @check_response
    def delete(self):
        return self.discovery.images().delete(project=self.project,
                                              image=self.name).execute()

    def list(self):
        image_list = self.discovery.images().list(
                project=self.project).execute()
        return image_list['items']

    def list_objects(self):
        storage = self.create_discovery(discovery=constants.STORAGE_DISCOVERY,
                                        scope=constants.STORAGE_SCOPE_RW,
                                        api_version=constants.API_V1)
        response = storage.objects().list(bucket=self.project).execute()
        return response.get('items')

    def to_dict(self):
        body = {
            'name': self.name,
            'rawDisk': {
                'source': self.url,
                'containerType': 'TAR'
            }
        }
        return body


@operation
@utils.throw_cloudify_exceptions
def create(image_name, image_path, **kwargs):
    gcp_config = utils.get_gcp_config()
    name = utils.get_final_resource_name(image_name)
    image = Image(gcp_config, ctx.logger, name)
    upload_image(image, image_path)
    ctx.instance.runtime_properties['name'] = image.name


@utils.create_resource
def upload_image(image, image_path):
    local_path = ctx.download_resource(image_path)
    image.upload_and_create(local_path)


@operation
@utils.retry_on_failure('Retrying deleting image')
@utils.throw_cloudify_exceptions
def delete(**kwargs):
    gcp_config = utils.get_gcp_config()
    name = ctx.instance.runtime_properties.get('name')
    image = Image(gcp_config, ctx.logger, name)
    utils.delete_if_not_external(image)
    ctx.instance.runtime_properties.pop('name')
