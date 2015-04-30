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
from cloudify import ctx
from cloudify.exceptions import NonRecoverableError
from cloudify.exceptions import RecoverableError
from googleapiclient.discovery import build
from oauth2client.client import SignedJwtAssertionCredentials

from plugin.gcp import utils


class GoogleCloudPlatform(object):
    def __init__(self, auth, project, scope):
        self.auth = auth
        self.project = project
        self.scope = scope
        self.compute = self.create_compute()

    def create_compute(self):
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
            raise RecoverableError(e.message)

    def create_instance(self,
                        instance_name,
                        agent_image,
                        machine_type='n1-standard-1',
                        network='default'):
        ctx.logger.info('Create instance')
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

        return self.compute.instances().insert(
            project=self.project['name'],
            zone=self.project['zone'],
            body=body).execute()

    def delete_instance(self, instance_name):
        ctx.logger.info('Delete instance')
        return self.compute.instances().delete(
            project=self.project['name'],
            zone=self.project['zone'],
            instance=instance_name).execute()

    def list_instances(self):
        ctx.logger.info("List instances")
        return self.compute.instances().list(
            project=self.project['name'],
            zone=self.project['zone']).execute()

    def wait_for_operation(self,
                           operation,
                           global_operation=False):
        ctx.logger.info('Wait for operation: {0}.'.format(operation))
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
                    raise NonRecoverableError(result['error'])
                ctx.logger.info('Done')
                return result
            else:
                time.sleep(1)

    def set_ip(self):
        instances = self.list_instances()
        item = utils.get_item_from_gcp_response(ctx.node.name, instances)
        ctx.instance.runtime_properties['ip'] = \
            item['networkInterfaces'][0]['networkIP']
        # only with one default network interface

    def create_network(self, network):
        ctx.logger.info('Create network')
        body = {
            "description": "Cloudify generated network",
            "name": network
        }
        return self.compute.networks().insert(project=self.project['name'],
                                              body=body).execute()

    def delete_network(self, network):
        ctx.logger.info('Delete network')
        return self.compute.networks().delete(project=self.project['name'],
                                              network=network).execute()

    def list_networks(self):
        ctx.logger.info('List networks')
        return self.compute.networks().list(
            project=self.project['name']).execute()

    def create_firewall_rule(self, network, firewall):
        ctx.logger.info('Create firewall rule')
        firewall = dict(firewall)
        firewall['network'] = \
            'global/networks/{0}'.format(network)
        firewall['name'] = utils.get_firewall_rule_name(network, firewall)
        return self.compute.firewalls().insert(project=self.project['name'],
                                               body=firewall).execute()

    def delete_firewall_rule(self, network, firewall):
        ctx.logger.info('Delete firewall rule')
        return self.compute.firewalls().delete(
            project=self.project['name'],
            firewall=utils.get_firewall_rule_name(network, firewall)).execute()

    def list_firewall_rules(self):
        ctx.logger.info('List firewall rules in project')
        return self.compute.firewalls().list(
            project=self.project['name']).execute()
