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
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from cloudify import ctx
from cloudify.decorators import operation
from cloudify.exceptions import NonRecoverableError

from .. import constants
from .. import utils
from cloudify_gcp.gcp import GoogleCloudPlatform
from cloudify_gcp.gcp import check_response


class SslCertificate(GoogleCloudPlatform):
    def __init__(self,
                 config,
                 logger,
                 name,
                 additional_settings=None,
                 private_key=None,
                 certificate=None):
        super(SslCertificate, self).__init__(config,
                                             logger,
                                             name,
                                             additional_settings,
                                             api_version=constants.API_BETA)
        self.private_key = private_key
        self.certificate = certificate

    def to_dict(self):
        self.body.update({
            'description': 'Cloudify generated SSL certificate',
            'name': self.name,
            'privateKey': self.private_key,
            'certificate': self.certificate
        })
        return self.body

    def get_self_url(self):
        return 'global/sslCertificates/{0}'.format(self.name)

    @check_response
    def get(self):
        return self.discovery.sslCertificates().get(
            project=self.project,
            sslCertificate=self.name).execute()

    @check_response
    def list(self):
        return self.discovery.sslCertificates().list(
            project=self.project).execute()

    @utils.async_operation(get=True)
    @check_response
    def create(self):
        return self.discovery.sslCertificates().insert(
            project=self.project,
            body=self.to_dict()).execute()

    @utils.async_operation()
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
    private_key_data = get_pem_data(private_key['type'], private_key['data'])
    certificate_data = get_pem_data(certificate['type'], certificate['data'])
    ssl_certificate = SslCertificate(config=gcp_config,
                                     logger=ctx.logger,
                                     name=name,
                                     private_key=private_key_data,
                                     certificate=certificate_data)
    utils.create(ssl_certificate)


@operation
@utils.retry_on_failure('Retrying deleting SSL certificate')
@utils.throw_cloudify_exceptions
def delete(**kwargs):
    gcp_config = utils.get_gcp_config()
    name = ctx.instance.runtime_properties.get('name')
    if name:
        ssl_certificate = SslCertificate(config=gcp_config,
                                         logger=ctx.logger,
                                         name=name)
        utils.delete_if_not_external(ssl_certificate)


def get_pem_data(resource_type, resource_data):
    if resource_type == 'text':
        return resource_data
    elif resource_type == 'file':
        pem_file_path = ctx.download_resource(resource_data)
        try:
            with open(pem_file_path) as pem_file:
                return pem_file.read()
        except IOError as error:
            raise NonRecoverableError(
                'Error during reading certificate file {0}: {1}'.format(
                    pem_file_path, error))

    else:
        raise NonRecoverableError(
            'Unknown type of certificate resource: {0}.'.format(resource_type))
