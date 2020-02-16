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

from cloudify import ctx
from cloudify.decorators import operation

from .. import constants
from .. import utils
from ..gcp import (
    check_response,
    GoogleCloudPlatform,
    )


class DNSZone(GoogleCloudPlatform):
    def __init__(self,
                 config,
                 logger,
                 name,
                 dns_name=None,
                 additional_settings=None,
                 ):
        """
        Create DNSZone object

        :param config: gcp auth file
        :param logger: logger object
        :param name: internal name for the dns zone
        :param dns_name: FQDN for the zone

        """
        super(DNSZone, self).__init__(
            config,
            logger,
            utils.get_gcp_resource_name(name),
            discovery='dns',
            scope='https://www.googleapis.com/auth/ndev.clouddns.readwrite',
            additional_settings=additional_settings,
            )
        self.name = name
        self.dns_name = dns_name

    @check_response
    def create(self):
        """
        Create GCP DNS Zone.
        Global operation.

        :return: REST response with operation responsible for the zone
        creation process and its status
        """
        self.logger.info("Create DNS Zone '{0}'".format(self.name))
        return self.discovery.managedZones().create(
                project=self.project,
                body=self.to_dict()).execute()

    @check_response
    def delete(self):
        """
        Delete GCP DNS Zone.
        Global operation

        :return: REST response with operation responsible for the zone
        deletion process and its status
        """
        self.logger.info("Delete DNS Zone '{0}'".format(self.name))
        return self.discovery.managedZones().delete(
            project=self.project,
            managedZone=self.name).execute()

    def to_dict(self):
        body = {
            'description': 'Cloudify generated DNS Zone',
            constants.NAME: self.name,
            'dnsName': self.dns_name,
        }
        self.body.update(body)
        return self.body

    def list_records(self, name=None, type=None):
        rrsets = []

        resources = self.discovery.resourceRecordSets()

        request = resources.list(
                project=self.project,
                managedZone=self.name,
                type=type,
                name='.'.join([name, self.dns_name]),
                )

        while request is not None:
            response = request.execute()

            rrsets.extend(response['rrsets'])

            request = resources.list_next(
                    previous_request=request,
                    previous_response=response)

        return rrsets

    def get(self):
        return self.discovery.managedZones().get(
            project=self.project,
            managedZone=self.name).execute()


@operation(resumable=True)
@utils.throw_cloudify_exceptions
def create(name, dns_name, additional_settings=None, **kwargs):
    if utils.resource_created(ctx, constants.NAME):
        return

    gcp_config = utils.get_gcp_config()
    if not name:
        name = ctx.node.id
    if not dns_name:
        dns_name = name
    name = utils.get_final_resource_name(name)

    dns_zone = DNSZone(
            gcp_config,
            ctx.logger,
            name,
            dns_name,
            additional_settings=additional_settings,
            )

    resource = utils.create(dns_zone)
    ctx.instance.runtime_properties.update(resource)


@operation(resumable=True)
@utils.retry_on_failure('Retrying deleting dns zone')
@utils.throw_cloudify_exceptions
def delete(**kwargs):
    gcp_config = utils.get_gcp_config()
    name = ctx.instance.runtime_properties.get(constants.NAME)
    if name:
        dns_zone = DNSZone(
                gcp_config,
                ctx.logger,
                name)
        utils.delete_if_not_external(dns_zone)

        if not utils.is_object_deleted(dns_zone):
            ctx.operation.retry('Zone is not yet deleted. Retrying:',
                                constants.RETRY_DEFAULT_DELAY)

        ctx.instance.runtime_properties.pop(constants.NAME, None)
