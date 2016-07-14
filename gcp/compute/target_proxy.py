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

from cloudify import ctx
from cloudify.decorators import operation
from cloudify.exceptions import NonRecoverableError

from gcp.compute import utils
from gcp.compute import constants
from gcp.gcp import GoogleCloudPlatform
from gcp.gcp import check_response


class TargetProxy(GoogleCloudPlatform):
    __metaclass__ = ABCMeta

    def __init__(self,
                 config,
                 logger,
                 name,
                 api_version,
                 url_map=None,
                 additional_settings=None):
        super(TargetProxy, self).__init__(config,
                                          logger,
                                          name,
                                          additional_settings,
                                          api_version=api_version)
        self.url_map = url_map

    @check_response
    def get(self):
        self_data = self.gcp_get_dict()
        return self._gcp_target_proxies().get(**self_data).execute()

    @check_response
    def list(self):
        return self._gcp_target_proxies().list(project=self.project).execute()

    @check_response
    def create(self):
        return self._gcp_target_proxies().insert(
            project=self.project,
            body=self.to_dict()).execute()

    @check_response
    @utils.sync_operation
    def delete(self):
        self_data = self.gcp_get_dict()
        return self._gcp_target_proxies().delete(**self_data).execute()

    @abstractmethod
    def get_self_url(self):
        pass

    @abstractmethod
    def gcp_get_dict(self):
        pass

    @abstractmethod
    def to_dict(self):
        pass

    @abstractmethod
    def _gcp_target_proxies(self):
        pass


class TargetHttpProxy(TargetProxy):
    def __init__(self,
                 config,
                 logger,
                 name,
                 additional_settings=None,
                 api_version=constants.API_V1,
                 url_map=None):
        super(TargetHttpProxy, self).__init__(config,
                                              logger,
                                              name,
                                              api_version,
                                              url_map,
                                              additional_settings)

    def get_self_url(self):
        return 'global/targetHttpProxies/{0}'.format(self.name)

    def gcp_get_dict(self):
        return {
            'project': self.project,
            'targetHttpProxy': self.name
        }

    def to_dict(self):
        self.body.update({
            'description': 'Cloudify generated TargetHttpProxy',
            'name': self.name,
            'urlMap': self.url_map
        })
        return self.body

    def _gcp_target_proxies(self):
        return self.discovery.targetHttpProxies()


class TargetHttpsProxy(TargetProxy):
    def __init__(self,
                 config,
                 logger,
                 name,
                 url_map=None,
                 ssl_certificate=None,
                 additional_settings=None):
        super(TargetHttpsProxy, self).__init__(config,
                                               logger,
                                               name,
                                               constants.API_BETA,
                                               url_map,
                                               additional_settings)
        self.ssl_certificate = ssl_certificate

    def get_self_url(self):
        return 'global/targetHttpsProxies/{0}'.format(self.name)

    def gcp_get_dict(self):
        return {
            'project': self.project,
            'targetHttpsProxy': self.name
        }

    def to_dict(self):
        self.body.update({
            'description': 'Cloudify generated TargetHttpsProxy',
            'name': self.name,
            'urlMap': self.url_map,
            'sslCertificates': [
                self.ssl_certificate
            ]
        })
        return self.body

    def _gcp_target_proxies(self):
        return self.discovery.targetHttpsProxies()


@operation
@utils.throw_cloudify_exceptions
def create(name, target_proxy_type, url_map, ssl_certificate,
           additional_settings, **kwargs):
    name = utils.get_final_resource_name(name)
    gcp_config = utils.get_gcp_config()
    target_proxy = target_proxy_of_type(target_proxy_type,
                                        config=gcp_config,
                                        logger=ctx.logger,
                                        name=name,
                                        url_map=url_map,
                                        ssl_certificate=ssl_certificate,
                                        additional_settings=additional_settings)
    utils.create(target_proxy)
    ctx.instance.runtime_properties[constants.NAME] = name
    ctx.instance.runtime_properties[constants.TARGET_PROXY_TYPE] = \
        target_proxy_type
    ctx.instance.runtime_properties[constants.SELF_URL] = \
        target_proxy.get_self_url()


@operation
@utils.retry_on_failure('Retrying deleting target proxy')
@utils.throw_cloudify_exceptions
def delete(**kwargs):
    gcp_config = utils.get_gcp_config()
    name = ctx.instance.runtime_properties.get(constants.NAME)
    target_proxy_type = ctx.instance.runtime_properties.get(
        constants.TARGET_PROXY_TYPE)

    if name:
        target_proxy = target_proxy_of_type(target_proxy_type,
                                            config=gcp_config,
                                            logger=ctx.logger,
                                            name=name)
        utils.delete_if_not_external(target_proxy)
        ctx.instance.runtime_properties.pop(constants.NAME, None)
        ctx.instance.runtime_properties.pop(constants.TARGET_PROXY_TYPE, None)
        ctx.instance.runtime_properties.pop(constants.SELF_URL, None)


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
