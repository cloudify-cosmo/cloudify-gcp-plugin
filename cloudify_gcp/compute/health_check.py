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
from abc import ABCMeta, abstractmethod
from copy import copy

from cloudify import ctx
from cloudify.decorators import operation
from cloudify.exceptions import NonRecoverableError

from .. import constants
from .. import utils
from cloudify_gcp.gcp import GoogleCloudPlatform
from cloudify_gcp.gcp import check_response


class HealthCheck(GoogleCloudPlatform):
    __metaclass__ = ABCMeta

    def __init__(self,
                 config,
                 logger,
                 name,
                 api_version,
                 name_keyword,
                 additional_settings=None):
        super(HealthCheck, self).__init__(config, logger,
                                          name, api_version=api_version)
        self.additional_settings = copy(additional_settings) or {}
        self.name_keyword = name_keyword

    def to_dict(self):
        body = {
            'description': 'Cloudify generated {0}'.format(self.name_keyword),
            'name': self.name
        }
        gcp_settings = {utils.camel_farm(key): value
                        for key, value in self.additional_settings.iteritems()}
        body.update(gcp_settings)
        return body

    @check_response
    def get(self):
        kwargs = {
            'project': self.project,
            self.name_keyword: self.name
        }
        return self._gcp_health_checks().get(**kwargs).execute()

    @utils.async_operation(get=True)
    @check_response
    def create(self):
        return self._gcp_health_checks().insert(
            project=self.project,
            body=self.to_dict()).execute()

    @check_response
    def list(self):
        return self._gcp_health_checks().list(project=self.project).execute()

    @utils.async_operation()
    @check_response
    def delete(self):
        kwargs = {
            'project': self.project,
            self.name_keyword: self.name
        }
        return self._gcp_health_checks().delete(**kwargs).execute()

    @abstractmethod
    def get_self_url(self):
        """Return URL endpoint for the health check type"""

    @abstractmethod
    def _gcp_health_checks(self):
        """return discovery object for the health check type"""


class HttpHealthCheck(HealthCheck):
    def __init__(self,
                 config,
                 logger,
                 name,
                 port=None,
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


class TcpHealthCheck(HealthCheck):
    def __init__(self,
                 config,
                 logger,
                 name,
                 port=None,
                 api_version=constants.API_V1,
                 additional_settings=None):
        super(TcpHealthCheck, self).__init__(
            config, logger, name, api_version,
            'healthCheck', additional_settings)

        self.port = port

    def get_self_url(self):
        return '{0}/projects/{1}/global/healthChecks/{2}'.format(
            self.api_version, self.project, self.name)

    def to_dict(self):
        body = {
            'description': 'Cloudify generated {0}'.format(self.name_keyword),
            'name': self.name,
            'type': 'TCP',
            'tcpHealthCheck': {'port': self.port}
        }
        gcp_settings = {utils.camel_farm(key): value
                        for key, value in self.additional_settings.iteritems()}
        body.update(gcp_settings)
        return body

    def _gcp_health_checks(self):
        return self.discovery.healthChecks()


class SslHealthCheck(HealthCheck):
    def __init__(self,
                 config,
                 logger,
                 name,
                 port=None,
                 api_version=constants.API_V1,
                 additional_settings=None):
        super(SslHealthCheck, self).__init__(
            config, logger, name, api_version,
            'healthCheck', additional_settings)

        self.port = port

    def get_self_url(self):
        return '{0}/projects/{1}/global/healthChecks/{2}'.format(
            self.api_version, self.project, self.name)

    def to_dict(self):
        body = {
            'description': 'Cloudify generated {0}'.format(self.name_keyword),
            'name': self.name,
            'type': 'SSL',
            'sslHealthCheck': {'port': self.port}
        }
        gcp_settings = {utils.camel_farm(key): value
                        for key, value in self.additional_settings.iteritems()}
        body.update(gcp_settings)
        return body

    def _gcp_health_checks(self):
        return self.discovery.healthChecks()


class HttpsHealthCheck(HealthCheck):
    def __init__(self,
                 config,
                 logger,
                 name,
                 port=None,
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
def create(name, health_check_type, port, additional_settings, **kwargs):
    name = utils.get_final_resource_name(name)
    gcp_config = utils.get_gcp_config()
    health_check = health_check_of_type(
            health_check_type,
            config=gcp_config,
            logger=ctx.logger,
            name=name,
            port=port,
            additional_settings=additional_settings)

    utils.create(health_check)


@operation
@utils.retry_on_failure('Retrying deleting health check')
@utils.throw_cloudify_exceptions
def delete(health_check_type, **kwargs):
    gcp_config = utils.get_gcp_config()
    name = ctx.instance.runtime_properties.get('name')
    health_check = health_check_of_type(health_check_type,
                                        config=gcp_config,
                                        logger=ctx.logger,
                                        name=name)

    utils.delete_if_not_external(health_check)


def health_check_of_type(health_check_type, **kwargs):
    if health_check_type == 'http':
        return HttpHealthCheck(**kwargs)
    elif health_check_type == 'https':
        return HttpsHealthCheck(**kwargs)
    elif health_check_type == 'tcp':
        return TcpHealthCheck(**kwargs)
    elif health_check_type == 'ssl':
        return SslHealthCheck(**kwargs)
    else:
        raise NonRecoverableError(
            'Unexpected type of health check: {}'.format(health_check_type))
