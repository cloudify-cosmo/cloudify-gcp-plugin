# #######
# Copyright (c) 2014-2020 Cloudify Platform Ltd. All rights reserved
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
from os.path import basename
from copy import copy

from cloudify import ctx
from cloudify.decorators import operation

from .. import utils
from .. import constants
from ..gcp import (
        check_response,
        GoogleCloudPlatform,
        )


class RegionBackendService(GoogleCloudPlatform):

    def __init__(self,
                 config,
                 logger,
                 name,
                 region=None,
                 health_check=None,
                 protocol=None,
                 additional_settings=None,
                 backends=None):
        super(RegionBackendService, self).__init__(
            config, logger, name, api_version=constants.API_V1)

        self.health_check = health_check
        self.additional_settings = copy(additional_settings) or {}
        self.backends = backends or []
        self.protocol = protocol
        self.region = region

    def to_dict(self):
        body = {
            'description': 'Cloudify generated backend service',
            constants.NAME: self.name,
            'healthChecks': [
                self.health_check
            ],
            'protocol': self.protocol
        }
        gcp_settings = {utils.camel_farm(key): value
                        for key, value in self.additional_settings.iteritems()}
        body.update(gcp_settings)
        return body

    def get_self_url(self):
        return '{0}/RegionBackendServices/{1}'.format(
            basename(self.region), self.name)

    @check_response
    def get(self):
        return self.discovery.regionBackendServices().get(
            project=self.project, region=basename(self.region),
            backendService=self.name).execute()

    @check_response
    def list(self):
        return self.discovery.regionBackendServices().list(
            project=self.project, region=basename(self.region)).execute()

    @utils.async_operation(get=True)
    @check_response
    def create(self):
        return self.discovery.regionBackendServices().insert(
            project=self.project, region=self.region,
            body=self.to_dict()).execute()

    @utils.async_operation()
    @check_response
    def delete(self):
        return self.discovery.regionBackendServices().delete(
            project=self.project, region=basename(self.region),
            backendService=self.name).execute()

    @check_response
    def set_backends(self, backends):
        body = {
            'backends': backends
        }
        self.backends = backends
        return self.discovery.regionBackendServices().patch(
            project=self.project,
            backendService=self.name,
            region=basename(self.region),
            body=body).execute()

    @utils.sync_operation
    def add_backend(self, current_backends, group_self_url):
        new_backend = {'group': group_self_url}
        for backend in current_backends:
            if backend.get('group') == group_self_url:
                backends = current_backends
                break
        else:
            backends = current_backends + [new_backend]
        return self.set_backends(backends)

    @utils.sync_operation
    def remove_backend(self, current_backends, group_self_url):
        backends = filter(lambda backend: backend['group'] != group_self_url,
                          current_backends)
        return self.set_backends(backends)


@operation(resumable=True)
@utils.throw_cloudify_exceptions
def create(name, region, health_check, protocol, additional_settings,
           **kwargs):
    if utils.resource_created(ctx, constants.NAME):
        return

    name = utils.get_final_resource_name(name)
    gcp_config = utils.get_gcp_config()
    backend_service = RegionBackendService(gcp_config,
                                           ctx.logger,
                                           name,
                                           region,
                                           health_check,
                                           protocol,
                                           additional_settings)

    utils.create(backend_service)


@operation(resumable=True)
@utils.retry_on_failure('Retrying deleting backend service')
@utils.throw_cloudify_exceptions
def delete(**kwargs):
    gcp_config = utils.get_gcp_config()
    name = ctx.instance.runtime_properties.get(constants.NAME)

    if name:
        backend_service = RegionBackendService(
            gcp_config,
            ctx.logger,
            name=name,
            region=ctx.instance.runtime_properties['region'])
        utils.delete_if_not_external(backend_service)


@operation(resumable=True)
@utils.throw_cloudify_exceptions
def add_backend(backend_service_name, group_self_url, **kwargs):
    _modify_backends(
            backend_service_name,
            group_self_url,
            RegionBackendService.add_backend)


@operation(resumable=True)
@utils.throw_cloudify_exceptions
def remove_backend(backend_service_name, group_self_url, **kwargs):
    _modify_backends(
            backend_service_name,
            group_self_url,
            RegionBackendService.remove_backend)


def _modify_backends(backend_service_name, group_self_url, modify_function):
    sprops = ctx.source.instance.runtime_properties
    gcp_config = utils.get_gcp_config()
    if backend_service_name and sprops.get('region'):
        backend_service = RegionBackendService(
            gcp_config,
            ctx.logger,
            name=backend_service_name,
            region=sprops['region'])
        backends = sprops.get('backends', [])
        modify_function(backend_service, backends, group_self_url)
        sprops.update(backend_service.get())
