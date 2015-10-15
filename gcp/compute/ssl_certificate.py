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

from gcp.compute import utils
from gcp.compute import constants
from gcp.gcp import GoogleCloudPlatform
from gcp.gcp import check_response


class SslCertificate(GoogleCloudPlatform):
    def __init__(self,
                 config,
                 logger,
                 name,
                 private_key=None,
                 certificate=None):
        super(SslCertificate, self).__init__(config, logger, name,
                                             api_version=constants.API_BETA)
        self.private_key = private_key
        self.certificate = certificate

    def to_dict(self):
        body = {
            'description': 'Cloudify generated SSL certificate',
            'name': self.name,
            'privateKey': self.private_key,
            'certificate': self.certificate
        }
        return body

    def get_self_url(self):
        return 'global/sslCertificates/{0}'.format(self.name)

    @check_response
    def get(self):
        return self.discovery.sslCertificates().get(
            project=self.project,
            sslCertificate=self.name).execute()

    @check_response
    @utils.sync_operation
    def create(self):
        return self.discovery.sslCertificates().insert(
            project=self.project,
            body=self.to_dict()).execute()

    @check_response
    def delete(self):
        return self.discovery.sslCertificates().delete(
            project=self.project,
            sslCertificate=self.name).execute()


@operation
@utils.throw_cloudify_exceptions
def create(name, private_key, certificate, **kwargs):
    name = utils.get_final_resource_name(name)
    gcp_config = utils.get_gcp_config()
    ssl_certificate = SslCertificate(config=gcp_config,
                                     logger=ctx.logger,
                                     name=name,
                                     private_key=private_key,
                                     certificate=certificate)
    utils.create(ssl_certificate)
    ctx.instance.runtime_properties[constants.NAME] = name
    ctx.instance.runtime_properties[constants.SELF_URL] = \
        ssl_certificate.get_self_url()


@operation
@utils.retry_on_failure('Retrying deleting SSL certificate')
@utils.throw_cloudify_exceptions
def delete(**kwargs):
    gcp_config = utils.get_gcp_config()
    name = ctx.instance.runtime_properties.get(constants.NAME)
    if name:
        ssl_certificate = SslCertificate(config=gcp_config,
                                         logger=ctx.logger,
                                         name=name)
        utils.delete_if_not_external(ssl_certificate)
        ctx.instance.runtime_properties.pop(constants.NAME, None)
        ctx.instance.runtime_properties.pop(constants.SELF_URL, None)
