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

from .. import utils
from ..gcp import check_response
from ..gcp import GoogleCloudPlatform


class Route(GoogleCloudPlatform):
    def __init__(
            self,
            config,
            logger,
            name,
            network,
            dest_range=None,
            tags=None,
            next_hop=None,
            priority=None,
            ):
        """
        Create Route object

        :param config: gcp auth file
        :param logger: logger object
        :param route: route dictionary having at least 'name' key

        """
        super(Route, self).__init__(
            config,
            logger,
            utils.get_gcp_resource_name(name))

        self.network = network
        self.name = utils.get_gcp_resource_name(
                name if name else ctx.instance.id)
        self.dest_range = dest_range
        self.tags = tags
        self.priority = priority

        if next_hop:
            self.hop_type = 'nextHopIp'
            self.hop_dest = next_hop
        else:
            rels = utils.get_relationships(
                    ctx,
                    filter_resource_types='instances',
                    )
            if rels:
                inst = rels[0]
                self.hop_type = 'nextHopInstance'
                self.hop_dest = inst.target.instance.runtime_properties[
                        'selfLink']
            else:
                # Hardcoded because this is the only gateway the API supports.
                # see
                # https://cloud.google.com/compute/docs/reference/latest/routes/insert#nextHopGateway
                self.hop_type = 'nextHopGateway'
                self.hop_dest = 'global/gateways/default-internet-gateway'

    @utils.async_operation(get=True)
    @check_response
    def create(self):
        """
        Create GCP route.
        Global operation.

        :return: REST response with operation responsible for the route
        creation process and its status
        """
        self.logger.info('Create route {0}'.format(self.name))
        return self.discovery.routes().insert(
                project=self.project,
                body=self.to_dict()).execute()

    @utils.async_operation()
    @check_response
    def delete(self):
        """
        Delete GCP route.
        Global operation

        :param route: route name
        :return: REST response with operation responsible for the route
        deletion process and its status
        """
        self.logger.info('Delete route {0}'.format(self.name))
        return self.discovery.routes().delete(
            project=self.project,
            route=self.name).execute()

    @check_response
    def get(self):
        """
        Get GCP route details.

        :return: REST response with operation responsible for the route
        details retrieval
        """
        self.logger.info('Get route {0} details'.format(self.name))
        return self.discovery.routes().get(
            project=self.project,
            route=self.name).execute()

    @check_response
    def list(self):
        """
        List routes.

        :return: REST response with list of routes in a project
        """
        self.logger.info('List routes in project {0}'.format(self.project))
        return self.discovery.routes().list(
            project=self.project).execute()

    def to_dict(self):
        body = {
            'description': 'Cloudify generated route',
            'name': self.name,
            'network': self.network,
            'tags': self.tags,
            'destRange': self.dest_range,
            'priority': self.priority,
            self.hop_type: self.hop_dest,
        }
        return body


@operation
@utils.throw_cloudify_exceptions
def create(dest_range, name, tags, next_hop, priority, **kwargs):
    gcp_config = utils.get_gcp_config()
    name = utils.get_final_resource_name(name)
    network = utils.get_network(ctx)

    route = Route(
            config=gcp_config,
            logger=ctx.logger,
            name=name,
            network=network,
            dest_range=dest_range,
            tags=tags,
            next_hop=next_hop,
            priority=priority,
            )

    utils.create(route)


@operation
@utils.throw_cloudify_exceptions
def delete(name=None, **kwargs):
    gcp_config = utils.get_gcp_config()
    props = ctx.instance.runtime_properties

    network = utils.get_network(ctx)
    if props.get('name', None):
        name = props['name']
    else:
        name = utils.get_final_resource_name(name)

    route = Route(
            gcp_config,
            ctx.logger,
            name,
            network,
            )

    utils.delete_if_not_external(route)
