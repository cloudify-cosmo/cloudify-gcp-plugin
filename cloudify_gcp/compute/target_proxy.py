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
from abc import ABCMeta, abstractmethod, abstractproperty

from cloudify import ctx
from cloudify.exceptions import NonRecoverableError

from .. import utils
from .. import constants
from ..utils import operation
from ..gcp import (
        check_response,
        GoogleCloudPlatform,
        )


class TargetProxy(GoogleCloudPlatform):
    __metaclass__ = ABCMeta

    def __init__(self,
                 config,
                 logger,
                 name,
                 api_version,
                 url_map=None):
        super(TargetProxy, self).__init__(config, logger,
                                          name, api_version=api_version)
        self.url_map = url_map

    @check_response
    def get(self):
        self_data = self.gcp_get_dict()
        return self._gcp_target_proxies().get(**self_data).execute()

    @check_response
    def list(self):
        return self._gcp_target_proxies().list(project=self.project).execute()

    @utils.async_operation(get=True)
    @check_response
    def create(self):
        return self._gcp_target_proxies().insert(
            project=self.project,
            body=self.to_dict()).execute()

    @utils.async_operation()
    @check_response
    @utils.sync_operation
    def delete(self):
        self_data = self.gcp_get_dict()
        return self._gcp_target_proxies().delete(**self_data).execute()

    @abstractproperty
    def kind(self):
        """The kind string which matches the resource from the API"""

    @abstractmethod
    def get_self_url(self):
        """Return URL component for the proxy"""

    @abstractmethod
    def gcp_get_dict(self):
        """Generate the resource representation for the proxy"""

    @abstractmethod
    def to_dict(self):
        """Generate the resource representation for the proxy"""

    @abstractmethod
    def _gcp_target_proxies(self):
        """Get the correct endpoind wrapper for the proxy type"""


class TargetHttpProxy(TargetProxy):
    kind = 'compute#targetHttpProxy'

    def __init__(self,
                 config,
                 logger,
                 name,
                 api_version=constants.API_V1,
                 url_map=None):
        super(TargetHttpProxy, self).__init__(config, logger, name,
                                              api_version, url_map)

    def get_self_url(self):
        return 'global/targetHttpProxies/{0}'.format(self.name)

    def gcp_get_dict(self):
        return {
            'project': self.project,
            'targetHttpProxy': self.name
        }

    def to_dict(self):
        return {
            'description': 'Cloudify generated TargetHttpProxy',
            'name': self.name,
            'urlMap': self.url_map
        }

    def _gcp_target_proxies(self):
        return self.discovery.targetHttpProxies()


class TargetHttpsProxy(TargetProxy):
    kind = 'compute#targetHttpsProxy'

    def __init__(self,
                 config,
                 logger,
                 name,
                 url_map=None,
                 ssl_certificate=None):
        super(TargetHttpsProxy, self).__init__(config, logger, name,
                                               constants.API_BETA, url_map)
        self.ssl_certificate = ssl_certificate

    def get_self_url(self):
        return 'global/targetHttpsProxies/{0}'.format(self.name)

    def gcp_get_dict(self):
        return {
            'project': self.project,
            'targetHttpsProxy': self.name
        }

    def to_dict(self):
        return {
            'description': 'Cloudify generated TargetHttpsProxy',
            'name': self.name,
            'urlMap': self.url_map,
            'sslCertificates': [
                self.ssl_certificate
            ]
        }

    def _gcp_target_proxies(self):
        return self.discovery.targetHttpsProxies()


@operation
@utils.throw_cloudify_exceptions
def create(name, target_proxy_type, url_map, ssl_certificate, **kwargs):
    name = utils.get_final_resource_name(name)
    gcp_config = utils.get_gcp_config()
    target_proxy = target_proxy_of_type(target_proxy_type,
                                        config=gcp_config,
                                        logger=ctx.logger,
                                        name=name,
                                        url_map=url_map,
                                        ssl_certificate=ssl_certificate)
    ctx.instance.runtime_properties['kind'] = target_proxy.kind

    utils.create(target_proxy)


@operation
@utils.retry_on_failure('Retrying deleting target proxy')
@utils.throw_cloudify_exceptions
def delete(**kwargs):
    gcp_config = utils.get_gcp_config()
    name = ctx.instance.runtime_properties.get('name')
    if ctx.instance.runtime_properties.get(
            'kind') == 'compute#targetHttpProxy':
        target_proxy_type = 'http'
    else:
        target_proxy_type = 'https'

    if name:
        target_proxy = target_proxy_of_type(target_proxy_type,
                                            config=gcp_config,
                                            logger=ctx.logger,
                                            name=name)

        utils.delete_if_not_external(target_proxy)


def creation_validation(*args, **kwargs):
    props = ctx.node.properties
    if not props['url_map']:
        raise NonRecoverableError('url_map must be specified')


def target_proxy_of_type(target_proxy_type, **kwargs):
    if target_proxy_type == 'http':
        if kwargs.get('ssl_certificate'):
            raise NonRecoverableError(
                'TargetHttpProxy should not have SSL certificate')
        kwargs.pop('ssl_certificate', None)
        return TargetHttpProxy(**kwargs)
    elif target_proxy_type == 'https':
        return TargetHttpsProxy(**kwargs)
    else:
        raise NonRecoverableError(
            'Unexpected type of target proxy: {}'.format(target_proxy_type))
