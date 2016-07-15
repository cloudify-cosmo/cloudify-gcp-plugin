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
from copy import copy

from cloudify import ctx
from cloudify.decorators import operation

from gcp.compute import utils
from gcp.compute import constants
from gcp.gcp import GoogleCloudPlatform
from gcp.gcp import check_response


class BackendService(GoogleCloudPlatform):

    def __init__(self,
                 config,
                 logger,
                 name,
                 health_check=None,
                 additional_settings=None,
                 backends=None):
        super(BackendService, self).__init__(config,
                                             logger,
                                             name,
                                             additional_settings,
                                             api_version=constants.API_BETA)
        self.health_check = health_check
        self.additional_settings = copy(additional_settings) or {}
        self.backends = backends or []

    def to_dict(self):
        self.body.update({
            'description': 'Cloudify generated backend service',
            'name': self.name,
            'healthChecks': [
                self.health_check
            ]
        })
        return self.body

    def backend_to_dict(self, group_self_url):
        return {
            'group': group_self_url
        }

    def get_self_url(self):
        return 'global/backendServices/{0}'.format(self.name)

    @check_response
    def get(self):
        return self.discovery.backendServices().get(
            project=self.project,
            backendService=self.name).execute()

    @check_response
    def list(self):
        return self.discovery.backendServices().list(
            project=self.project).execute()

    @check_response
    def create(self):
        return self.discovery.backendServices().insert(
            project=self.project,
            body=self.to_dict()).execute()

    @check_response
    def delete(self):
        return self.discovery.backendServices().delete(
            project=self.project,
            backendService=self.name).execute()

    @check_response
    def set_backends(self, backends):
        body = {
            'backends': backends
        }
        self.backends = backends
        return self.discovery.backendServices().patch(
            project=self.project,
            backendService=self.name,
            body=body).execute()

    def add_backend(self, current_backends, group_self_url):
        new_backend = self.backend_to_dict(group_self_url)
        backends = current_backends + [new_backend]
        return self.set_backends(backends)

    def remove_backend(self, current_backends, group_self_url):
        backends = filter(lambda backend: backend['group'] == group_self_url,
                          current_backends)
        return self.set_backends(backends)


@operation
@utils.throw_cloudify_exceptions
def create(name, health_check, additional_settings, **kwargs):
    name = utils.get_final_resource_name(name)
    gcp_config = utils.get_gcp_config()
    backend_service = BackendService(gcp_config,
                                     ctx.logger,
                                     name,
                                     health_check,
                                     additional_settings)
    utils.create(backend_service)
    ctx.instance.runtime_properties[constants.NAME] = name
    ctx.instance.runtime_properties[constants.SELF_URL] = \
        backend_service.get_self_url()
    ctx.instance.runtime_properties[constants.BACKENDS] = []


@operation
@utils.retry_on_failure('Retrying deleting backend service')
@utils.throw_cloudify_exceptions
def delete(**kwargs):
    gcp_config = utils.get_gcp_config()
    name = ctx.instance.runtime_properties.get(constants.NAME, None)
    if name:
        backend_service = BackendService(gcp_config,
                                         ctx.logger,
                                         name=name)
        utils.delete_if_not_external(backend_service)
        ctx.instance.runtime_properties.pop(constants.NAME, None)
        ctx.instance.runtime_properties.pop(constants.SELF_URL, None)
        ctx.instance.runtime_properties.pop(constants.BACKENDS, None)


@operation
@utils.throw_cloudify_exceptions
def add_backend(backend_service_name, group_self_url, **kwargs):
    __modify_backends(backend_service_name,
                      group_self_url,
                      BackendService.add_backend)


@operation
@utils.throw_cloudify_exceptions
def remove_backend(backend_service_name, group_self_url, **kwargs):
    __modify_backends(backend_service_name,
                      group_self_url,
                      BackendService.remove_backend)


def __modify_backends(backend_service_name, group_self_url, modify_function):
    gcp_config = utils.get_gcp_config()
    backend_service = BackendService(gcp_config,
                                     ctx.logger,
                                     backend_service_name)
    backends = ctx.source.instance.runtime_properties[constants.BACKENDS]
    modify_function(backend_service, backends, group_self_url)
    ctx.source.instance.runtime_properties[constants.BACKENDS] = \
        backend_service.backends
