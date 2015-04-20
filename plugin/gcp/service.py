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

from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client.tools import run_flow, argparser
from googleapiclient.discovery import build
from cloudify import ctx

storage = None


def init_oauth(config):
    ctx.logger.info("Init OAuth")
    flow = flow_from_clientsecrets(config['client_secret'],
                                   scope=config['gcp_scope'])
    return flow


def list_instances(config, compute):
    ctx.logger.info("List instances")
    return compute.instances().list(project=config['project'],
                                    zone=config['zone']).execute()


def authenticate(flow, storage_path):
    ctx.logger.info("Get credentials")
    global storage
    storage = Storage(storage_path)
    credentials = storage.get()
    flags = argparser.parse_args(args=[])
    if credentials is None or credentials.invalid:
        ctx.logger.info("Credentials are invalid or they are missing."
                        " Trying to generate...")
        credentials = run_flow(flow, storage, flags)
    return credentials


def create_instance(name, config_input, compute):
    ctx.logger.info("Create instance")
    source_disk_image = config_input['agent_image']
    machine_type = "zones/%s/machineTypes/n1-standard-1" % config_input['zone']

    config = {
        'name': name,
        'machineType': machine_type,

        # Specify the boot disk and the image to use as a source.
        'disks': [
            {
                'boot': True,
                'autoDelete': True,
                'initializeParams': {
                    'sourceImage': source_disk_image,
                }
            }
        ],

        # Specify a network interface with NAT to access the public
        # internet.
        'networkInterfaces': [{
            'network': 'global/networks/default',
            'accessConfigs': [
                {'type': 'ONE_TO_ONE_NAT', 'name': 'External NAT'}
            ]
        }],

        # Allow the instance to access cloud storage and logging.
        'serviceAccounts': [{
            'email': 'default',
            'scopes': [
                'https://www.googleapis.com/auth/devstorage.read_write',
                'https://www.googleapis.com/auth/logging.write'
            ]
        }],

        # Metadata is readable from the instance and allows you to
        # pass configuration from deployment scripts to instances.
        'metadata': {
            'items': [{
                # Every project has a default Cloud Storage bucket that's
                # the same name as the project.
                'key': 'bucket',
                'value': config_input['project']
            }]
        }
    }

    return compute.instances().insert(
        project=config_input['project'],
        zone=config_input['zone'],
        body=config).execute()


def delete_instance(name, config, compute):
    ctx.logger.info("Delete instance")
    return compute.instances().delete(
        project=config['project'],
        zone=config['zone'],
        instance=name).execute()


def wait_for_operation(config, operation, compute):
    ctx.logger.info("Wait for operation")
    while True:
        result = compute.zoneOperations().get(
            project=config['project'],
            zone=config['zone'],
            operation=operation).execute()
        if result['status'] == 'DONE':
            if 'error' in result:
                raise Exception(result['error'])
            return result
        else:
            time.sleep(1)


def compute(credentials):
    return build('compute', 'v1', credentials=credentials)


def set_ip(config, compute):
    instances = list_instances(config, compute)
    item = get_instance_from_list(ctx.node.name, instances)
    ctx.instance.runtime_properties['ip'] = item['networkInterfaces'][0][
        'networkIP'] # only with one default network interface


def get_instance_from_list(name, instances):
    for item in instances.get('items'):
        ctx.logger.info(str(item))
        if item.get('name') == name:
            return item
    return None  #throw an exception
