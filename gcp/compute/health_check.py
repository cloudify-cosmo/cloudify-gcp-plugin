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
from abc import ABCMeta, abstractmethod
from copy import copy

from cloudify import ctx
from cloudify.decorators import operation
from cloudify.exceptions import NonRecoverableError

from gcp.compute import utils
from gcp.compute import constants
from gcp.gcp import GoogleCloudPlatform
from gcp.gcp import check_response


class HealthCheck(GoogleCloudPlatform):
    __metaclass__ = ABCMeta

    def __init__(self,
                 config,
                 logger,
                 name,
                 api_version,
                 name_keyword,
                 additional_settings=None):
        super(HealthCheck, self).__init__(config,
                                          logger,
                                          name,
                                          additional_settings=
                                          additional_settings,
                                          api_version=api_version)
        self.name_keyword = name_keyword

    def to_dict(self):
        self.body.update({
            'description': 'Cloudify generated {0}'.format(self.name_keyword),
            'name': self.name
        })
        return self.body

    @check_response
    def get(self):
        kwargs = {
            'project': self.project,
            self.name_keyword: self.name
        }
        return self._gcp_health_checks().get(**kwargs).execute()

    @check_response
    def create(self):
        return self._gcp_health_checks().insert(
            project=self.project,
            body=self.to_dict()).execute()

    @check_response
    def list(self):
        return self._gcp_health_checks().list(project=self.project).execute()

    @check_response
    def delete(self):
        kwargs = {
            'project': self.project,
            self.name_keyword: self.name
        }
        return self._gcp_health_checks().delete(**kwargs).execute()

    @abstractmethod
    def get_self_url(self):
        pass

    @abstractmethod
    def _gcp_health_checks(self):
        pass


class HttpHealthCheck(HealthCheck):
    def __init__(self,
                 config,
                 logger,
                 name,
                 api_version=constants.API_V1,
                 additional_settings=None):
        super(HttpHealthCheck, self).__init__(
            config, logger, name, api_version,
            'httpHealthCheck', additional_settings)

    def get_self_url(self):
        return '{0}/projects/{1}/global/httpHealthChecks/{2}'.format(
            self.api_version, self.project, self.name)

    def _gcp_health_checks(self):
        return self.discovery.httpHealthChecks()


class HttpsHealthCheck(HealthCheck):
    def __init__(self,
                 config,
                 logger,
                 name,
                 additional_settings=None):
        super(HttpsHealthCheck, self).__init__(
            config, logger, name, constants.API_BETA,
            'httpsHealthCheck', additional_settings)

    def get_self_url(self):
        return '{0}/projects/{1}/global/httpsHealthChecks/{2}'.format(
            self.api_version, self.project, self.name)

    def _gcp_health_checks(self):
        return self.discovery.httpsHealthChecks()


@operation
@utils.throw_cloudify_exceptions
def create(name, health_check_type, additional_settings, **kwargs):
    name = utils.get_final_resource_name(name)
    gcp_config = utils.get_gcp_config()
    health_check = health_check_of_type(health_check_type,
                                        config=gcp_config,
                                        logger=ctx.logger,
                                        name=name,
                                        additional_settings=additional_settings)
    utils.create(health_check)
    ctx.instance.runtime_properties[constants.NAME] = name
    ctx.instance.runtime_properties[constants.HEALTH_CHECK_TYPE] = \
        health_check_type
    ctx.instance.runtime_properties[constants.SELF_URL] = \
        health_check.get_self_url()


@operation
@utils.retry_on_failure('Retrying deleting health check')
@utils.throw_cloudify_exceptions
def delete(**kwargs):
    gcp_config = utils.get_gcp_config()
    name = ctx.instance.runtime_properties.get(constants.NAME)
    health_check_type = ctx.instance.runtime_properties.get(
        constants.HEALTH_CHECK_TYPE)

    if name:
        health_check = health_check_of_type(health_check_type,
                                            config=gcp_config,
                                            logger=ctx.logger,
                                            name=name)
        utils.delete_if_not_external(health_check)
        ctx.instance.runtime_properties.pop(constants.NAME, None)
        ctx.instance.runtime_properties.pop(constants.HEALTH_CHECK_TYPE, None)
        ctx.instance.runtime_properties.pop(constants.SELF_URL, None)


def health_check_of_type(health_check_type, **kwargs):
    if health_check_type == 'http':
        return HttpHealthCheck(**kwargs)
    elif health_check_type == 'https':
        return HttpsHealthCheck(**kwargs)
    else:
        raise NonRecoverableError(
            'Unexpected type of health check: {}'.format(health_check_type))
