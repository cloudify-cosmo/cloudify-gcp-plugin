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
from googleapiclient.discovery import build
from oauth2client.client import SignedJwtAssertionCredentials


def create_instance(compute,
                    project,
                    zone,
                    instance_name,
                    agent_image,
                    machine_type='n1-standard-1',
                    network='default'):
    ctx.logger.info('Create instance')
    machine_type = 'zones/{0}/machineTypes/{1}'.format(zone, machine_type)

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
                'value': project
            }]
        }
    }

    return compute.instances().insert(
        project=project,
        zone=zone,
        body=body).execute()


def delete_instance(compute, project, zone, instance_name):
    ctx.logger.info('Delete instance')
    return compute.instances().delete(
        project=project,
        zone=zone,
        instance=instance_name).execute()


def list_instances(compute, project, zone):
    ctx.logger.info("List instances")
    return compute.instances().list(project=project,
                                    zone=zone).execute()


def wait_for_operation(compute,
                       project,
                       zone,
                       operation,
                       global_operation=False):
    ctx.logger.info('Wait for operation: {0}.'.format(operation))
    while True:
        if global_operation:
            result = compute.globalOperations().get(
                project=project,
                operation=operation).execute()
        else:
            result = compute.zoneOperations().get(
                project=project,
                zone=zone,
                operation=operation).execute()
        if result['status'] == 'DONE':
            if 'error' in result:
                raise NonRecoverableError(result['error'])
            ctx.logger.info('Done')
            return result
        else:
            time.sleep(1)


def compute(service_account, scope):
    Crypto.Random.atfork()
    with open(service_account) as f:
        account_data = json.load(f)
    credentials = SignedJwtAssertionCredentials(account_data['client_email'],
                                                account_data['private_key'],
                                                scope=scope)
    http = httplib2.Http()
    credentials.authorize(http)
    return build('compute', 'v1', http=http)


def set_ip(compute, config):
    instances = list_instances(compute, config['project'], config['zone'])
    item = _get_item_from_gcp_response(ctx.node.name, instances)
    ctx.instance.runtime_properties['ip'] = \
        item['networkInterfaces'][0]['networkIP']
    # only with one default network interface


def _get_item_from_gcp_response(name, items):
    for item in items.get('items'):
        if item.get('name') == name:
            return item
    return None


def create_network(compute, project, network):
    ctx.logger.info('Create network')
    body = {
        "description": "Cloudify generated network",
        "name": network
    }
    return compute.networks().insert(project=project,
                                     body=body).execute()


def delete_network(compute, project, network):
    ctx.logger.info('Delete network')
    return compute.networks().delete(project=project,
                                     network=network).execute()


def list_networks(compute, project):
    ctx.logger.info('List networks')
    return compute.networks().list(project=project).execute()


def create_firewall_rule(compute, project, network, firewall):
    ctx.logger.info('Create firewall rule')
    firewall['network'] = \
        'global/networks/{0}'.format(network)
    firewall['name'] = '{0}-{1}'.format(network, firewall['name'])
    # should be changed in node runtime properties
    return compute.firewalls().insert(project=project,
                                      body=firewall).execute()


def delete_firewall_rule(compute, project, firewall_name):
    ctx.logger.info('Delete firewall rule')
    return compute.firewalls().delete(
        project=project,
        firewall=firewall_name).execute()


def list_firewall_rules(compute, project):
    ctx.logger.info('List firewall rules in project')
    return compute.firewalls().list(project=project).execute()
