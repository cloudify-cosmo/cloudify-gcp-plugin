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

from os.path import basename

from cloudify import ctx
from cloudify.exceptions import NonRecoverableError

from .. import utils
from ..utils import operation
from ..gcp import check_response
from ..gcp import GoogleCloudPlatform


class SubNetwork(GoogleCloudPlatform):
    def __init__(self,
                 config,
                 logger,
                 name,
                 region,
                 subnet=None,
                 network=None,
                 ):
        """
        Create SubNetwork object

        :param config: gcp auth file
        :param logger: logger object
        :param name: name of the subnetwork
        :param region: region which this subnetwork will be in
        :param subnet: CIDR range description for this subnet

        """
        super(SubNetwork, self).__init__(
            config,
            logger,
            utils.get_gcp_resource_name(name))
        self.region = region
        self.subnet = subnet
        self.network = network

    @utils.async_operation(get=True)
    @check_response
    def create(self):
        """
        Create GCP subnetwork.
        Global operation.

        :return: REST response with operation responsible for the subnetwork
        creation process and its status
        """
        self.logger.info('Create subnetwork {0}'.format(self.name))
        return self.discovery.subnetworks().insert(
                project=self.project,
                region=self.region,
                body=self.to_dict()).execute()

    @utils.async_operation()
    @check_response
    def delete(self):
        """
        Delete GCP subnetwork.
        Global operation

        :return: REST response with operation responsible for the network
        deletion process and its status
        """
        self.logger.info('Delete subnetwork {0}'.format(self.name))
        return self.discovery.subnetworks().delete(
            project=self.project,
            region=basename(self.region),
            subnetwork=self.name,
            ).execute()

    @check_response
    def get(self):
        """
        Get GCP subnetwork details.

        :return: REST response with operation responsible for the subnetwork
        details retrieval
        """
        self.logger.info('Get subnetwork {0} details'.format(self.name))
        return self.discovery.subnetworks().get(
            project=self.project,
            region=self.region,
            subnetwork=self.name).execute()

    @check_response
    def list(self):
        """
        List subnetworks.

        :return: REST response with list of subnetworks in a project
        """
        self.logger.info(
                'List subnetworks in project {0}'.format(self.project))
        return self.discovery.subnetworks().list(
            project=self.project).execute()

    def to_dict(self):
        body = {
            'description': 'Cloudify generated subnetwork',
            'name': self.name,
            'network': self.network,
            'ipCidrRange': self.subnet,
        }
        self.body.update(body)
        return self.body


@operation
@utils.throw_cloudify_exceptions
def create(name, region, subnet, **kwargs):
    gcp_config = utils.get_gcp_config()
    name = utils.get_final_resource_name(name)
    network = utils.get_relationships(
            ctx,
            filter_relationships='cloudify.gcp.relationships'
                                 '.contained_in_network'
            )[0].target.instance

    subnetwork = SubNetwork(
            gcp_config,
            ctx.logger,
            name,
            region,
            subnet,
            network.runtime_properties['selfLink'],
            )

    utils.create(subnetwork)


@operation
@utils.throw_cloudify_exceptions
def delete(**kwargs):
    gcp_config = utils.get_gcp_config()
    name = ctx.instance.runtime_properties.get('name', None)
    subnetwork = SubNetwork(
            gcp_config,
            ctx.logger,
            name=name,
            region=ctx.instance.runtime_properties['region']
            )

    utils.delete_if_not_external(subnetwork)


def creation_validation(**kwargs):
    if not ctx.node.properties['region']:
        raise NonRecoverableError("region must be supplied")

    types = ('cloudify.gcp.relationships.contained_in_network',
             'cloudify.gcp.nodes.Network')
    rels = utils.get_relationships(ctx, *types)

    if len(rels) != 1:
        raise NonRecoverableError(
                "SubNetwork must be contained in a '{1}' using the '{0}' "
                "relationship".format(*types))

    if not ctx.node.properties['use_external_resource']:
        network = rels[0].target
        if network.node.properties['auto_subnets']:
            raise NonRecoverableError(
                "Custom Subnets are not supported on auto_subnets Networks")

        # If the subnet is an external resource then specifying the
        # subnet range is not necessary
        if not ctx.node.properties['subnet']:
            raise NonRecoverableError("subnet must be supplied")
