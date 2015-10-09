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
    GCP_TRANSLATION = {
        'port_name': 'portName',
        'protocol': 'protocol',
        'timeout_sec': 'timeoutSec'
    }

    def __init__(self,
                 config,
                 logger,
                 name,
                 health_check=None,
                 additional_settings=None):
        super(BackendService, self).__init__(config, logger, name,
                                             api_version=constants.API_BETA)
        self.health_check = health_check
        self.additional_settings = copy(additional_settings) or {}

    def to_dict(self):
        body = {
            'description': 'Cloudify generated backend service',
            'name': self.name,
            'healthChecks': [
                self.health_check
            ]
        }
        gcp_settings = {self.GCP_TRANSLATION[key]: value
                        for key, value in self.additional_settings.iteritems()}
        body.update(gcp_settings)
        return body

    @check_response
    def get(self):
        return self.discovery.backendServices().get(
            project=self.project,
            backendService=self.name).execute()

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
