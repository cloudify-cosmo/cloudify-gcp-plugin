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
from cloudify.exceptions import RecoverableError
from googleapiclient.errors import HttpError

from .. import utils
from .. import constants
from ..gcp import check_response
from ..gcp import GoogleCloudPlatform


class Network(GoogleCloudPlatform):
    def __init__(self,
                 config,
                 logger,
                 name,
                 auto_subnets=True,
                 additional_settings=None
                 ):
        """
        Create Network object

        :param config: gcp auth file
        :param logger: logger object
        :param network: network dictionary having at least 'name' key

        """
        super(Network, self).__init__(
            config,
            logger,
            utils.get_gcp_resource_name(name),
            additional_settings,
            )
        self.iprange = None
        self.auto_subnets = auto_subnets

    @utils.async_operation(get=True)
    @check_response
    def create(self):
        """
        Create GCP network.
        Global operation.

        :return: REST response with operation responsible for the network
        creation process and its status
        """
        self.logger.info('Create network {0}'.format(self.name))
        return self.discovery.networks().insert(project=self.project,
                                                body=self.to_dict()).execute()

    @utils.async_operation()
    @check_response
    def delete(self):
        """
        Delete GCP network.
        Global operation

        :param network: network name
        :return: REST response with operation responsible for the network
        deletion process and its status
        """
        self.logger.info('Delete network {0}'.format(self.name))
        return self.discovery.networks().delete(
            project=self.project,
            network=self.name).execute()

    @check_response
    def get(self):
        """
        Get GCP network details.

        :return: REST response with operation responsible for the network
        details retrieval
        """
        self.logger.info('Get network {0} details'.format(self.name))
        return self.discovery.networks().get(
            project=self.project,
            network=self.name).execute()

    @check_response
    def list(self):
        """
        List networks.

        :return: REST response with list of networks in a project
        """
        self.logger.info('List networks in project {0}'.format(self.project))
        return self.discovery.networks().list(
            project=self.project).execute()

    def to_dict(self):
        self.body.update({
            'description': 'Cloudify generated network',
            'name': self.name,
            'autoCreateSubnetworks': self.auto_subnets,
        })
        return self.body


class NetworkPeering(GoogleCloudPlatform):
    def __init__(self,
                 config,
                 logger,
                 name,
                 network,
                 peerNetwork,
                 autoCreateRoutes=True
                 ):
        """
        Create VPN Network Peering object

        :param config: gcp auth file
        :param logger: logger object
        :param name:  name of peering
        :param network name of the network resource to add peering to
        :param peerNetwork name of  the peer network
        :param autoCreateRoutes `hether Google Compute Engine manages
               the routes automatically
        """
        super(NetworkPeering, self).__init__(
            config,
            logger,
            utils.get_gcp_resource_name(name),
            additional_settings=None,
            )
        self.network = network
        self.peerNetwork = peerNetwork
        self.autoCreateRoutes = autoCreateRoutes

    @check_response
    def create(self):
        """
        Create a peering to the specified network
        Global operation.

        :return: REST response with operation responsible for the peering
        creation process and its status
        """
        self.logger.info('VPN peering network {0}'.format(self.name))
        return self.discovery.networks().addPeering(
            project=self.project,
            network=self.network,
            body={
                "name": self.name,
                "peerNetwork": 'global/networks/{}'.format(self.peerNetwork),
                "autoCreateRoutes": self.autoCreateRoutes}).execute()

    @utils.async_operation()
    @check_response
    def delete(self):
        """
        Delete a peering from the specified network.
        Global operation

        :return: REST response with operation responsible for the network
        deletion process and its status
        """
        self.logger.info('Delete peering network {0}'.format(self.name))
        return self.discovery.networks().removePeering(
            project=self.project,
            network=self.network,
            body={"name": self.name}).execute()


@operation
@utils.throw_cloudify_exceptions
def create(name, auto_subnets, additional_settings, **kwargs):
    gcp_config = utils.get_gcp_config()
    name = utils.get_final_resource_name(name)

    network = Network(
            config=gcp_config,
            logger=ctx.logger,
            auto_subnets=auto_subnets,
            name=name,
            additional_settings=additional_settings,
            )

    ctx.instance.runtime_properties[constants.RESOURCE_ID] = network.name
    ctx.instance.runtime_properties['name'] = network.name
    utils.create(network)


@operation
@utils.throw_cloudify_exceptions
def delete(name, **kwargs):
    gcp_config = utils.get_gcp_config()
    props = ctx.instance.runtime_properties

    if props.get('name'):
        name = props['name']
    else:
        name = utils.get_final_resource_name(name)

    network = Network(
            gcp_config,
            ctx.logger,
            name)

    utils.delete_if_not_external(network)
    ctx.instance.runtime_properties[constants.RESOURCE_ID] = None


@operation
@utils.throw_cloudify_exceptions
def add_peering(name, network, peerNetwork, autoCreateRoutes, **kwargs):
    gcp_config = utils.get_gcp_config()
    name = utils.get_final_resource_name(name)

    peer = NetworkPeering(
            config=gcp_config,
            logger=ctx.logger,
            name=name,
            network=network,
            peerNetwork=peerNetwork,
            autoCreateRoutes=autoCreateRoutes)
    try:
        utils.create(peer)
    except HttpError as e:
        # sometimes we got a try again error from GCP
        # "There is a peering operation in progress on the local or
        # peer network.Try again later."
        raise RecoverableError(e.message)
    ctx.instance.runtime_properties[constants.RESOURCE_ID] = peer.name


@operation
@utils.throw_cloudify_exceptions
def remove_peering(name, network, peerNetwork,  **kwargs):
    gcp_config = utils.get_gcp_config()
    props = ctx.instance.runtime_properties

    if props.get('name'):
        name = props['name']
    else:
        name = utils.get_final_resource_name(name)

    if props.get('network'):
        network = props['network']
    else:
        network = utils.get_final_resource_name(network)

    if props.get('peerNetwork'):
        peerNetwork = props['peerNetwork']
    else:
        peerNetwork = utils.get_final_resource_name(peerNetwork)

    peer = NetworkPeering(
            config=gcp_config,
            logger=ctx.logger,
            name=name,
            network=network,
            peerNetwork=peerNetwork)

    utils.delete_if_not_external(peer)
    ctx.instance.runtime_properties[constants.RESOURCE_ID] = None
