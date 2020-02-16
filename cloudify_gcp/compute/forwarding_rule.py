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
from os.path import basename

from cloudify import ctx
from cloudify.decorators import operation
from cloudify.exceptions import NonRecoverableError

from .. import utils
from .. import constants
from ..gcp import (
        check_response,
        GoogleCloudPlatform,
        )


class ForwardingRule(GoogleCloudPlatform):

    def __init__(self,
                 config,
                 logger,
                 name,
                 region=None,
                 scheme=None,
                 ports=None,
                 network=None,
                 subnet=None,
                 backend_service=None,
                 target_proxy=None,
                 port_range=None,
                 ip_address=None,
                 additional_settings=None):
        super(ForwardingRule, self).__init__(
                config,
                logger,
                name,
                additional_settings=additional_settings)
        self.target_proxy = target_proxy
        self.port_range = port_range
        self.ip_address = ip_address
        self.region = region
        self.scheme = scheme
        self.ports = ports
        self.network = network
        self.subnet = subnet
        self.backend_service = backend_service

    def to_dict(self):
        self.body.update({
            'description': 'Cloudify generated Global Forwarding Rule',
            constants.NAME: self.name,
            'loadBalancingScheme': self.scheme.upper(),
        })

        # internal
        if self.ports:
            self.body['ports'] = self.ports
        if self.network:
            self.body['network'] = self.network
        if self.subnet:
            self.body['subnetwork'] = self.subnet
        if self.backend_service:
            self.body['backendService'] = self.backend_service

        # external
        if self.port_range:
            self.body['portRange'] = self.port_range
        if self.target_proxy:
            self.body['target'] = self.target_proxy
        if self.ip_address:
            self.body['IPAddress'] = self.ip_address

        self.logger.info(repr(self.body))

        return self.body

    @check_response
    def get(self):
        return self.discovery.forwardingRules().get(
            project=self.project, region=basename(self.region),
            forwardingRule=self.name).execute()

    @check_response
    def list(self):
        return self.discovery.forwardingRules().list(
            project=self.project, region=basename(self.region)).execute()

    @utils.async_operation(get=True)
    @check_response
    def create(self):
        if self.scheme.lower() != 'internal':
            required_fileds = ['target_proxy', 'port_range', 'ip_address']
        else:
            required_fileds = ['backend_service']
        for name in required_fileds:
            if not getattr(self, name):
                raise NonRecoverableError(
                    'Forwarding Rule missing {}'.format(name))

        return self.discovery.forwardingRules().insert(
            project=self.project, region=self.region,
            body=self.to_dict()).execute()

    @utils.async_operation()
    @check_response
    def delete(self):
        return self.discovery.forwardingRules().delete(
            project=self.project, region=basename(self.region),
            forwardingRule=self.name).execute()


def creation_validation(**kwargs):
    props = ctx.node.properties

    if not props['target_proxy']:
        rels = utils.get_relationships(
            ctx,
            filter_relationships='cloudify.gcp.relationships.'
            'forwarding_rule_connected_to_target_proxy',
            filter_nodes='cloudify.gcp.nodes.TargetProxy')
        if not rels:
            raise NonRecoverableError(
                    'Must supply a target proxy, '
                    'either using the `target_proxy` property '
                    'or the `cloudify.gcp.relationships.'
                    'forwarding_rule_connected_to_target_proxy` relationship.')


@operation(resumable=True)
@utils.throw_cloudify_exceptions
def create(name, region, scheme, ports, network, subnet, backend_service,
           target_proxy, port_range, ip_address, additional_settings,
           **kwargs):
    if utils.resource_created(ctx, constants.NAME):
        return

    name = utils.get_final_resource_name(name)
    gcp_config = utils.get_gcp_config()

    if not target_proxy and scheme.lower() != 'internal':
        rel = utils.get_relationships(
                ctx,
                filter_relationships='cloudify.gcp.relationships.'
                'forwarding_rule_connected_to_target_proxy')[0]
        target_proxy = rel.target.instance.runtime_properties['selfLink']

    forwarding_rule = ForwardingRule(
            gcp_config,
            ctx.logger,
            name,
            region,
            scheme,
            ports,
            network,
            subnet,
            backend_service,
            target_proxy,
            port_range,
            ip_address,
            additional_settings=additional_settings)
    utils.create(forwarding_rule)


@operation(resumable=True)
@utils.retry_on_failure('Retrying deleting global forwarding rule')
@utils.throw_cloudify_exceptions
def delete(**kwargs):
    gcp_config = utils.get_gcp_config()
    name = ctx.instance.runtime_properties.get(constants.NAME)
    if name:
        forwarding_rule = ForwardingRule(
            gcp_config,
            ctx.logger,
            name=name,
            region=ctx.instance.runtime_properties['region'])
        utils.delete_if_not_external(forwarding_rule)
