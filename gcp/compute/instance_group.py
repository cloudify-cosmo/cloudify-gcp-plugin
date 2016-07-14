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


class InstanceGroup(GoogleCloudPlatform):
    def __init__(self,
                 config,
                 logger,
                 name,
                 additional_settings=None,
                 named_ports=None):
        super(InstanceGroup, self).__init__(config,
                                            logger,
                                            name,
                                            additional_settings)
        self.network = config['network']
        self.named_ports = named_ports or []
        self.self_url = None

    def to_dict(self):
        self.body.update({
            'description': 'Cloudify generated instance group',
            'name': self.name,
            'network': 'global/networks/{0}'.format(self.network),
            'namedPorts': self.named_ports
        })
        return self.body

    def instance_to_dict(self, instance_name):
        url = 'zones/{0}/instances/{1}'.format(self.zone, instance_name)
        return {
            'instances': [
                {
                    'instance': url
                }
            ]
        }

    def get_self_url(self):
        if not self.self_url:
            self.self_url = self.get()['selfLink']
        return self.self_url

    @check_response
    def get(self):
        return self.discovery.instanceGroups().get(
            project=self.project,
            zone=self.zone,
            instanceGroup=self.name).execute()

    @check_response
    def list(self):
        return self.discovery.instanceGroups().list(
            project=self.project,
            zone=self.zone).execute()

    @check_response
    def create(self):
        return self.discovery.instanceGroups().insert(
            project=self.project,
            zone=self.zone,
            body=self.to_dict()).execute()

    @check_response
    def delete(self):
        return self.discovery.instanceGroups().delete(
            project=self.project,
            zone=self.zone,
            instanceGroup=self.name).execute()

    @check_response
    def add_instance(self, instance_name):
        return self.discovery.instanceGroups().addInstances(
            project=self.project,
            zone=self.zone,
            instanceGroup=self.name,
            body=self.instance_to_dict(instance_name)).execute()

    @check_response
    def remove_instance(self, instance_name):
        return self.discovery.instanceGroups().removeInstances(
            project=self.project,
            zone=self.zone,
            instanceGroup=self.name,
            body=self.instance_to_dict(instance_name)).execute()


@operation
@utils.throw_cloudify_exceptions
def create(name, named_ports, additional_settings, **kwargs):
    name = utils.get_final_resource_name(name)
    gcp_config = utils.get_gcp_config()
    instance_group = InstanceGroup(gcp_config,
                                   ctx.logger,
                                   name=name,
                                   named_ports=named_ports,
                                   additional_settings=additional_settings)

    utils.create(instance_group)
    ctx.instance.runtime_properties[constants.NAME] = name
    ctx.instance.runtime_properties[constants.SELF_URL] = \
        instance_group.get_self_url()


@operation
@utils.retry_on_failure('Retrying deleting instance group')
@utils.throw_cloudify_exceptions
def delete(**kwargs):
    gcp_config = utils.get_gcp_config()
    name = ctx.instance.runtime_properties.get(constants.NAME, None)
    if name:
        instance_group = InstanceGroup(gcp_config,
                                       ctx.logger,
                                       name=name)
        utils.delete_if_not_external(instance_group)
        ctx.instance.runtime_properties.pop(constants.NAME, None)
        ctx.instance.runtime_properties.pop(constants.SELF_URL, None)


@operation
@utils.throw_cloudify_exceptions
def add_to_instance_group(instance_group_name, instance_name, **kwargs):
    gcp_config = utils.get_gcp_config()
    instance_group = InstanceGroup(gcp_config,
                                   ctx.logger,
                                   name=instance_group_name)
    instance_group.add_instance(instance_name)


@operation
@utils.throw_cloudify_exceptions
def remove_from_instance_group(instance_group_name, instance_name, **kwargs):
    gcp_config = utils.get_gcp_config()
    instance_group = InstanceGroup(gcp_config,
                                   ctx.logger,
                                   name=instance_group_name)
    instance_group.remove_instance(instance_name)
