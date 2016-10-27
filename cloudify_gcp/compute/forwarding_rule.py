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
from cloudify.exceptions import NonRecoverableError

from .. import utils
from ..utils import operation
from ..gcp import (
        check_response,
        GoogleCloudPlatform,
        )


class BaseForwardingRule(GoogleCloudPlatform):
    __metaclass__ = ABCMeta

    def __init__(self,
                 config,
                 logger,
                 name,
                 target_proxy=None,
                 port_range=None,
                 ip_address=None,
                 additional_settings=None):
        super(BaseForwardingRule, self).__init__(
                config,
                logger,
                name,
                additional_settings=additional_settings)
        self.target_proxy = target_proxy
        self.port_range = port_range
        self.ip_address = ip_address

    @abstractmethod
    def _get_endpoint(self):
        """Return the endpoint object for this type"""

    def to_dict(self):
        self.body.update({
            'description': 'Cloudify generated Global Forwarding Rule',
            'name': self.name,
            'target': self.target_proxy,
            'portRange': self.port_range,
            'IPAddress': self.ip_address
        })
        return self.body

    @check_response
    def get(self):
        return self._get_endpoint().get(
            project=self.project,
            forwardingRule=self.name).execute()

    @check_response
    def list(self):
        return self._get_endpoint().list(
            project=self.project).execute()

    @utils.async_operation(get=True)
    @check_response
    def create(self):
        for name in 'target_proxy', 'port_range', 'ip_address':
            if not getattr(self, name):
                raise NonRecoverableError(
                    'Forwarding Rule missing {}'.format(name))

        return self._get_endpoint().insert(
            project=self.project,
            body=self.to_dict()).execute()

    @utils.async_operation()
    @check_response
    def delete(self):
        return self._get_endpoint().delete(
            project=self.project,
            forwardingRule=self.name).execute()


class ForwardingRule(BaseForwardingRule):
    def _get_endpoint(self):
        return self.discovery.forwardingRules()


class GlobalForwardingRule(BaseForwardingRule):
    def _get_endpoint(self):
        return self.discovery.globalForwardingRules()


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


@operation
@utils.throw_cloudify_exceptions
def create(name, target_proxy, port_range,
           ip_address, additional_settings, **kwargs):
    name = utils.get_final_resource_name(name)
    gcp_config = utils.get_gcp_config()

    if not target_proxy:
        rel = utils.get_relationships(
                ctx,
                filter_relationships='cloudify.gcp.relationships.'
                'forwarding_rule_connected_to_target_proxy')[0]
        target_proxy = rel.target.instance.runtime_properties['selfLink']

    forwarding_rule = GlobalForwardingRule(
            gcp_config,
            ctx.logger,
            name,
            target_proxy,
            port_range,
            ip_address,
            additional_settings=additional_settings)
    utils.create(forwarding_rule)


@operation
@utils.retry_on_failure('Retrying deleting global forwarding rule')
@utils.throw_cloudify_exceptions
def delete(**kwargs):
    gcp_config = utils.get_gcp_config()
    name = ctx.instance.runtime_properties.get('name')
    if name:
        forwarding_rule = GlobalForwardingRule(gcp_config,
                                               ctx.logger,
                                               name=name)
        utils.delete_if_not_external(forwarding_rule)
