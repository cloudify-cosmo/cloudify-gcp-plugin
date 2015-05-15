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
from functools import wraps
from plugin.gcp import utils
from plugin.gcp.service import GoogleCloudPlatform
from plugin.gcp.service import GCPError


def blocking(default):
    def inner(func):
        def _decorator(self, *args, **kwargs):
            blocking = kwargs.get('blocking', default)
            response = func(self, *args, **kwargs)
            if blocking:
                self.wait_for_operation(response['name'])
            else:
                return response
        return wraps(func)(_decorator)
    return inner


class FirewallRule(GoogleCloudPlatform):
    def __init__(self,
                 config,
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
        super(FirewallRule, self).__init__(config, logger)
        self.firewall = firewall
        self.network = network
        self.firewall['name'] = self.get_name()
        self.name = self.firewall['name']

    def get_name(self):
        """
        Prefix firewall rule name with network name

        :return: network prefixed firewall rule name
        """
        name = '{0}-{1}'.format(self.network, self.firewall['name'])
        return utils.get_gcp_resource_name(name)

    @blocking(True)
    def create(self):
        """
        Create GCP firewall rule in a GCP network.
        Global operation.

        :return: REST response with operation responsible for the firewall rule
        creation process and its status
        """
        self.logger.info('Create firewall rule')
        self.firewall['network'] = 'global/networks/{0}'.format(self.network)
        return self.compute.firewalls().insert(
            project=self.project,
            body=self.firewall).execute()

    @blocking(True)
    def delete(self):
        """
        Delete GCP firewall rule from GCP network.
        Global operation.

        :return: REST response with operation responsible for the firewall rule
        deletion process and its status
        """
        self.logger.info('Delete firewall rule')
        return self.compute.firewalls().delete(
            project=self.project,
            firewall=self.firewall['name']).execute()

    @blocking(True)
    def update(self):
        self.logger.info('Update firewall rule')
        return self.compute.firewalls().update(
            project=self.project,
            firewall=self.firewall['name'],
            body=self.firewall).execute()

    def list(self):
        """
        List GCP firewall rules in all networks.

        :return: REST response with list of firewall rules in a project
        """
        self.logger.info('List firewall rules in project')
        return self.compute.firewalls().list(
            project=self.project).execute()

    def wait_for_operation(self, operation, global_operation=True):
        super(FirewallRule, self).wait_for_operation(operation,
                                                     global_operation)


class Network(GoogleCloudPlatform):
    def __init__(self,
                 config,
                 logger,
                 network):
        super(Network, self).__init__(config, logger)
        self.network = network
        self.name = utils.get_gcp_resource_name(network['name'])

    @blocking(True)
    def create(self):
        """
        Create GCP network.
        Global operation.

        :return: REST response with operation responsible for the network
        creation process and its status
        """
        self.logger.info('Create network')
        return self.compute.networks().insert(project=self.project,
                                              body=self.to_dict()).execute()

    @blocking(True)
    def delete(self):
        """
        Delete GCP network.
        Global operation

        :param network: network name
        :return: REST response with operation responsible for the network
        deletion process and its status
        """
        self.logger.info('Delete network')
        return self.compute.networks().delete(
            project=self.project,
            network=self.name).execute()

    def list(self):
        """
        List networks.

        :return: REST response with list of networks in a project
        """
        self.logger.info('List networks')
        return self.compute.networks().list(
            project=self.project).execute()

    def wait_for_operation(self, operation, global_operation=True):
        super(Network, self).wait_for_operation(operation, global_operation)

    def to_dict(self):
        body = {
            'description': 'Cloudify generated network',
            'name': self.name
        }
        return body


class Instance(GoogleCloudPlatform):
    def __init__(self,
                 config,
                 logger,
                 instance_name,
                 image=None,
                 machine_type=None,
                 startup_script=None,
                 tags=[]):
        super(Instance, self).__init__(config, logger)
        self.project = config['project']
        self.zone = config['zone']
        self.name = utils.get_gcp_resource_name(instance_name)
        self.image = image
        self.machine_type = machine_type if machine_type else 'n1-standard-1'
        self.network = config['network']
        self.startup_script = startup_script
        self.tags = tags

    @blocking(True)
    def create(self, startup_script=None):
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
            project=self.project,
            zone=self.zone,
            body=body).execute()

    @blocking(True)
    def delete(self):
        """
        Delete GCP instance.
        Zone operation.

        :return: REST response with operation responsible for the instance
        deletion process and its status
        """
        self.logger.info('Delete instance')
        return self.compute.instances().delete(
            project=self.project,
            zone=self.zone,
            instance=self.name).execute()

    @blocking(True)
    def set_tags(self, tags):
        # each tag should be RFC1035 compliant
        self.logger.info('Set tags')
        self.tags.extend(tags)
        self.tags = list(set(self.tags))
        fingerprint = self.get()["tags"]["fingerprint"]
        return self.compute.instances().setTags(
            project=self.project,
            zone=self.zone,
            instance=self.name,
            body={"items": self.tags, "fingerprint": fingerprint}).execute()

    def get(self):
        self.logger.info("Get instance details")
        return self.compute.instances().get(
            instance=self.name,
            project=self.project,
            zone=self.zone).execute()

    def list(self):
        """
        List GCP instances.
        Zone operation.

        :return: REST response with a list of instances and its details
        """
        self.logger.info("List instances")
        return self.compute.instances().list(
            project=self.project,
            zone=self.zone).execute()

    def wait_for_operation(self, operation, global_operation=False):
        super(Instance, self).wait_for_operation(operation, global_operation)

    def to_dict(self):
        body = {
            'name': self.name,
            'machineType': 'zones/{0}/machineTypes/{1}'.format(
                self.zone,
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
            'networkInterfaces': [
                {'network': 'global/networks/{0}'.format(self.network),
                 'accessConfigs': [{'type': 'ONE_TO_ONE_NAT',
                                    'name': 'External NAT'}]}],
            'serviceAccounts': [
                {'email': 'default',
                 'scopes': [
                     'https://www.googleapis.com/auth/devstorage.read_write',
                     'https://www.googleapis.com/auth/logging.write']}],
            'metadata': {
                'items': [
                    {'key': 'bucket', 'value': self.project}]
            }
        }
        if self.tags:
            body['tags'] = {"items": self.tags}
        return body
