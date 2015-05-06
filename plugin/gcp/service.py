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

import time
import json

import Crypto
import httplib2
from googleapiclient.discovery import build
from oauth2client.client import SignedJwtAssertionCredentials

from plugin.gcp import utils


class GoogleCloudPlatform(object):
    """
    Class using google-python-api-client library to connect to Google Cloud
    Platform.
    """
    def __init__(self, auth, project, scope, logger):
        """
        GoogleCloudPlatform class constructor.
        Create compute object that will be making
        Google Cloud Platform Compute API calls.

        :param auth: path to service account JSON file
        :param project: dictionary with project properties
        :param scope: scope string of GCP connection
        :param logger: logger object that the class methods will be logging to
        :return:
        """
        self.auth = auth
        self.project = project
        self.scope = scope
        self.compute = self.create_compute()
        self.logger = logger.getChild('GCP')

    def create_compute(self):
        """
        Create Google Cloud Compute object and perform authentication.

        :return: compute object
        :raise: GCPError if there is a problem with service account JSON file:
        e.g. the file is not under the given path or it has wrong permissions
        """
        Crypto.Random.atfork()
        try:
            with open(self.auth) as f:
                account_data = json.load(f)
            credentials = SignedJwtAssertionCredentials(
                account_data['client_email'],
                account_data['private_key'],
                scope=self.scope)
            http = httplib2.Http()
            credentials.authorize(http)
            return build('compute', 'v1', http=http)
        except IOError as e:
            self.logger.error(str(e))
            raise GCPError(str(e))

    def create_instance(self,
                        instance_name,
                        agent_image,
                        machine_type='n1-standard-1',
                        network='default',
                        startup_script=None):
        """
        Create GCP VM instance with given parameters.
        Zone operation.

        :param instance_name: name of the instance
        :param agent_image: id of the image to create instance from
        :param machine_type: GCP machine type, default 'n1-standard-1',
        ref. https://cloud.google.com/compute/docs/machine-types
        :param network: network name, default 'default'
        :param startup_script: shell script to be run on instance startup,
        default None
        :return: REST response with operation responsible for the instance
        creation process and its status
        :raise: GCPError if there is any problem with startup script file:
        e.g. the file is not under the given path or it has wrong permissions
        """
        self.logger.info('Create instance')
        machine_type = 'zones/{0}/machineTypes/{1}'.format(
            self.project['zone'],
            machine_type)

        body = {
            'name': instance_name,
            'machineType': machine_type,

            'disks': [
                {
                    'boot': True,
                    'autoDelete': True,
                    'initializeParams': {
                        'sourceImage': agent_image
                    }
                }
            ],
            'networkInterfaces': [{
                'network': 'global/networks/{0}'.format(network),
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

        if startup_script is not None:
            try:
                with open(startup_script, 'r') as script:
                    item = {
                        'key': 'startup-script',
                        'value': script
                    }
                    body['metadata']['items'].append(item)
            except IOError as e:
                self.logger.error(str(e))
                raise GCPError(str(e))

        return self.compute.instances().insert(
            project=self.project['name'],
            zone=self.project['zone'],
            body=body).execute()

    def delete_instance(self, instance_name):
        """
        Delete GCP instance.
        Zone operation.

        :param instance_name: name of the instance to be deleted
        :return: REST response with operation responsible for the instance
        deletion process and its status
        """
        self.logger.info('Delete instance')
        return self.compute.instances().delete(
            project=self.project['name'],
            zone=self.project['zone'],
            instance=instance_name).execute()

    def list_instances(self):
        """
        List GCP instances.
        Zone operation.

        :return: REST response with a list of instances and its details
        """
        self.logger.info("List instances")
        return self.compute.instances().list(
            project=self.project['name'],
            zone=self.project['zone']).execute()

    def wait_for_operation(self,
                           operation,
                           global_operation=False):
        """
        Method waiting with active polling (sleep(1)) until the given operation
        finishes (changes status to DONE).
        Handles all operation: zone and global.

        :param operation: operation name
        :param global_operation: indicator of global operation, default False
        :return: REST response with operation properties and status
        :raise: GCPError if the server response contains error message
        """
        self.logger.info('Wait for operation: {0}.'.format(operation))
        while True:
            if global_operation:
                result = self.compute.globalOperations().get(
                    project=self.project['name'],
                    operation=operation).execute()
            else:
                result = self.compute.zoneOperations().get(
                    project=self.project['name'],
                    zone=self.project['zone'],
                    operation=operation).execute()
            if result['status'] == 'DONE':
                if 'error' in result:
                    self.logger.error('Response with error')
                    raise GCPError(result['error'])
                self.logger.info('Operation finished: {0}'.format(operation))
                return result
            else:
                time.sleep(1)

    def create_network(self, network):
        """
        Create GCP network.
        Global operation.

        :param network: name of the network
        :return: REST response with operation responsible for the network
        creation process and its status
        """
        self.logger.info('Create network')
        body = {
            'description': 'Cloudify generated network',
            'name': network
        }
        return self.compute.networks().insert(project=self.project['name'],
                                              body=body).execute()

    def delete_network(self, network):
        """
        Delete GCP network.
        Global operation

        :param network: network name
        :return: REST response with operation responsible for the network
        deletion process and its status
        """
        self.logger.info('Delete network')
        return self.compute.networks().delete(project=self.project['name'],
                                              network=network).execute()

    def list_networks(self):
        """
        List networks.

        :return: REST response with list of networks in a project
        """
        self.logger.info('List networks')
        return self.compute.networks().list(
            project=self.project['name']).execute()

    def create_firewall_rule(self, network, firewall):
        """
        Create GCP firewall rule in a GCP network.
        Global operation.

        :param network: network name the firewall rule is connected to
        :param firewall: firewall dictionary with a following structure:
        firewall = {'name': 'firewallname',
                    'allowed: [{ 'IPProtocol': 'tcp', 'ports': ['80']}],
                    'sourceRanges':['0.0.0.0/0'],
                    'sourceTags':['tag'], (optional)
                    'targetTags':['tag2'] (optional)
                    }
        ref. https://cloud.google.com/compute/docs/reference/latest/firewalls
        :return: REST response with operation responsible for the firewall rule
        creation process and its status
        """
        self.logger.info('Create firewall rule')
        firewall = dict(firewall)
        firewall['network'] = \
            'global/networks/{0}'.format(network)
        firewall['name'] = utils.get_firewall_rule_name(network, firewall)
        return self.compute.firewalls().insert(project=self.project['name'],
                                               body=firewall).execute()

    def delete_firewall_rule(self, network, firewall):
        """
        Delete GCP firewall rule from GCP network.
        Global operation.

        :param network: network name the firewall rule is connected to
        :param firewall: firewall dictionary
        :return: REST response with operation responsible for the firewall rule
        deletion process and its status
        """
        self.logger.info('Delete firewall rule')
        return self.compute.firewalls().delete(
            project=self.project['name'],
            firewall=utils.get_firewall_rule_name(network, firewall)).execute()

    def list_firewall_rules(self):
        """
        List GCP firewall rules in all networks.

        :return: REST response with list of firewall rules in a project
        """
        self.logger.info('List firewall rules in project')
        return self.compute.firewalls().list(
            project=self.project['name']).execute()

    def update_project_ssh_keypair(self, user, ssh_key):
        """
        Update project SSH keypair. Add new keypair to project's
        common instance metadata.
        Global operation.

        :param user: user the key belongs to
        :param ssh_key: key belonging to the user
        :return: REST response with operation responsible for the sshKeys
        addition to project metadata process and its status
        """
        self.logger.info('Update project sshKeys metadata')
        key_name = 'key'
        key_value = 'sshKeys'
        commonInstanceMetadata = self.get_common_instance_metadata()
        if commonInstanceMetadata.get('items') is None:
            item = [{key_name: key_value,
                    'value': '{0}:{1}'.format(user, ssh_key)}]
            commonInstanceMetadata['items'] = item
        else:
            item = utils.get_item_from_gcp_response(
                key_name, key_value, commonInstanceMetadata)
            item['value'] = '{0}\n{1}:{2}'.format(item['value'], user, ssh_key)
        return self.compute.projects().setCommonInstanceMetadata(
            project=self.project['name'],
            body=commonInstanceMetadata).execute()

    def get_common_instance_metadata(self):
        """
        Get project's common instance metadata.

        :return: CommonInstanceMetadata list extracted from REST response get
        project metadata.
        """
        self.logger.info('Get commonInstanceMetadata')
        metadata = self.compute.projects().get(
            project=self.project['name']).execute()
        return metadata['commonInstanceMetadata']


class GCPError(Exception):
    """
    Exception raised from GoogleCloudPlatform class.
    """
    def __init__(self, message):
        super(GCPError, self).__init__(message)
