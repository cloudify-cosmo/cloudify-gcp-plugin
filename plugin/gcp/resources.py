########
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
from functools import wraps
from plugin.gcp import utils
from plugin.gcp.service import GoogleCloudPlatform
from plugin.gcp.service import GCPError


def if_blocking(func):
    def _decorator(self, *args, **kwargs):
        blocking = kwargs.get('blocking', True)
        response = func(self, *args, **kwargs)
        if blocking:
            self.wait_for_operation(response['name'])
        else:
            return response
    return wraps(func)(_decorator)


class FirewallRule(GoogleCloudPlatform):
    SOURCE_TAGS = 'sourceTags'
    SOURCE_RANGES = 'sourceRanges'
    TARGET_TAGS = 'targetTags'
    ALLOWED = 'allowed'
    IPPROTOCOL = 'IPProtocol'
    PORTS = 'ports'
    NAME = 'name'

    def __init__(self,
                 auth,
                 project,
                 logger,
                 firewall,
                 network):
        """

        :param auth:
        :param project:
        :param logger:
        :param firewall: firewall dictionary with a following structure:
        firewall = {'name': 'firewallname',
                    'allowed: [{ 'IPProtocol': 'tcp', 'ports': ['80']}],
                    'sourceRanges':['0.0.0.0/0'],
                    'sourceTags':['tag'], (optional)
                    'targetTags':['tag2'] (optional)
                    }
        ref. https://cloud.google.com/compute/docs/reference/latest/firewalls
        :param network: network name the firewall rule is connected to
        :return:
        """
        super(FirewallRule, self).__init__(auth, project, logger)
        self.firewall = firewall
        self.network = network
        self.firewall['name'] = self.get_name()
        self.name = self.firewall['name']

    def add_source_tag(self, tag):
        source_tags = self.firewall.get(self.SOURCE_TAGS, [])
        self.firewall[self.SOURCE_TAGS] = source_tags.append(tag)

    def remove_source_tag(self, tag):
        source_tags = self.firewall.get(self.SOURCE_TAGS, [])
        source_tags.remove(tag)  # error if not there

    def add_target_tag(self, tag):
        target_tags = self.firewall.get(self.TARGET_TAGS, [])
        target_tags.append(tag)

    def remove_target_tag(self, tag):
        target_tags = self.firewall.get(self.TARGET_TAGS, [])
        target_tags.remove(tag)  # error if not there

    def add_source_ranges(self, cidr_family):
        source_ranges = self.firewall.get(self.SOURCE_RANGES, [])
        source_ranges.append(cidr_family)

    def add_allowed(self, protocol, ports):
        allowed = self.firewall.get(self.ALLOWED, [])
        allowed.append({self.IPPROTOCOL: protocol, self.PORTS: ports})
        self.firewall[self.ALLOWED] = allowed.append(allowed)

    def get_name(self):
        """
        Prefix firewall rule name with network name

        :return: network prefixed firewall rule name
        """
        name = '{0}-{1}'.format(self.network, self.firewall['name'])
        return utils.get_gcp_resource_name(name)

    @if_blocking
    def create(self, blocking=True):
        """
        Create GCP firewall rule in a GCP network.
        Global operation.

        :return: REST response with operation responsible for the firewall rule
        creation process and its status
        """
        self.logger.info('Create firewall rule')
        self.firewall['network'] = 'global/networks/{0}'.format(self.network)
        return self.compute.firewalls().insert(
            project=self.project['name'],
            body=self.firewall).execute()

    @if_blocking
    def delete(self, blocking=True):
        """
        Delete GCP firewall rule from GCP network.
        Global operation.

        :return: REST response with operation responsible for the firewall rule
        deletion process and its status
        """
        self.logger.info('Delete firewall rule')
        return self.compute.firewalls().delete(
            project=self.project['name'],
            firewall=self.firewall['name']).execute()

    def list(self):
        """
        List GCP firewall rules in all networks.

        :return: REST response with list of firewall rules in a project
        """
        self.logger.info('List firewall rules in project')
        return self.compute.firewalls().list(
            project=self.project['name']).execute()

    def wait_for_operation(self, operation, global_operation=True):
        super(FirewallRule, self).wait_for_operation(operation,
                                                     global_operation)


class Network(GoogleCloudPlatform):
    def __init__(self,
                 auth,
                 project,
                 logger,
                 network):
        super(Network, self).__init__(auth, project, logger)
        self.network = utils.get_gcp_resource_name(network)
        self.network_fullname = 'global/networks/{0}'.format(network)

    @if_blocking
    def create(self, blocking=True):
        """
        Create GCP network.
        Global operation.

        :return: REST response with operation responsible for the network
        creation process and its status
        """
        self.logger.info('Create network')
        return self.compute.networks().insert(project=self.project['name'],
                                              body=self.to_dict()).execute()

    @if_blocking
    def delete(self, blocking=True):
        """
        Delete GCP network.
        Global operation

        :param network: network name
        :return: REST response with operation responsible for the network
        deletion process and its status
        """
        self.logger.info('Delete network')
        return self.compute.networks().delete(
            project=self.project['name'],
            network=self.network).execute()

    def list(self):
        """
        List networks.

        :return: REST response with list of networks in a project
        """
        self.logger.info('List networks')
        return self.compute.networks().list(
            project=self.project['name']).execute()

    def wait_for_operation(self, operation, global_operation=True):
        super(Network, self).wait_for_operation(operation, global_operation)

    def to_dict(self):
        body = {
            'description': 'Cloudify generated network',
            'name': self.network
        }
        return body


class Instance(GoogleCloudPlatform):
    def __init__(self,
                 auth,
                 project,
                 logger,
                 instance_name,
                 image=None,
                 machine_type=None,
                 network=None,
                 startup_script=None):
        super(Instance, self).__init__(auth, project, logger)
        self.project = project
        self.name = utils.get_gcp_resource_name(instance_name)
        self.image = image
        self.machine_type = machine_type if machine_type else 'n1-standard-1'
        self.network = network if network else 'default'
        self.startup_script = startup_script
        self.tags = []

    @if_blocking
    def create(self, startup_script=None, blocking=True):
        """
        Create GCP VM instance with given parameters.
        Zone operation.

        :param startup_script: shell script to be run on instance startup,
        default None
        :return: REST response with operation responsible for the instance
        creation process and its status
        :raise: GCPError if there is any problem with startup script file:
        e.g. the file is not under the given path or it has wrong permissions
        """
        self.logger.info('Create instance')
        body = self.to_dict()

        if startup_script is not None:
            try:
                with open(startup_script, 'r') as script:
                    item = {
                        'key': 'startup-script',
                        'value': script.read()
                    }
                    body['metadata']['items'].append(item)
            except IOError as e:
                self.logger.error(str(e))
                raise GCPError(str(e))

        return self.compute.instances().insert(
            project=self.project['name'],
            zone=self.project['zone'],
            body=body).execute()

    @if_blocking
    def delete(self, blocking=True):
        """
        Delete GCP instance.
        Zone operation.

        :return: REST response with operation responsible for the instance
        deletion process and its status
        """
        self.logger.info('Delete instance')
        return self.compute.instances().delete(
            project=self.project['name'],
            zone=self.project['zone'],
            instance=self.name).execute()

    @if_blocking
    def set_tags(self, tags, blocking=True):
        # each tag should be RFC1035 compliant
        self.logger.info('Set tags')
        self.tags.append(tags)
        self.tags = list(set(self.tags))
        return self.compute.instances().setTags(
            project=self.project['name'],
            zone=self.project['zone'],
            instance=self.name,
            body={"items": self.tags}
        )

    def list(self):
        """
        List GCP instances.
        Zone operation.

        :return: REST response with a list of instances and its details
        """
        self.logger.info("List instances")
        return self.compute.instances().list(
            project=self.project['name'],
            zone=self.project['zone']).execute()

    def wait_for_operation(self, operation, global_operation=False):
        super(Instance, self).wait_for_operation(operation, global_operation)

    def to_dict(self):
        body = {
            'name': self.name,
            'machineType': 'zones/{0}/machineTypes/{1}'.format(
                self.project['zone'],
                self.machine_type),

            'disks': [
                {
                    'boot': True,
                    'autoDelete': True,
                    'initializeParams': {
                        'sourceImage': self.image
                    }
                }
            ],
            'networkInterfaces': [{
                'network': 'global/networks/{0}'.format(self.network),
                'accessConfigs': [
                    {'type': 'ONE_TO_ONE_NAT', 'name': 'External NAT'}
                ]
            }],
            'serviceAccounts': [{
                'email': 'default',
                'scopes': [
                    'https://www.googleapis.com/auth/devstorage.read_write',
                    'https://www.googleapis.com/auth/logging.write'
                ]
            }],
            'metadata': {
                'items': [{
                    'key': 'bucket',
                    'value': self.project['name']
                }]
            }
        }
        if self.tags:
            body['tags'] = self.tags
        return body
