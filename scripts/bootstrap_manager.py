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
import sys
import logging

import yaml

from plugin.gcp.service import GoogleCloudPlatform
from plugin.gcp import utils

CONFIG = 'inputs_gcp.yaml'
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
logger = logging.getLogger()


def run(config):
    resource_register = {}
    gcp = None
    try:
        gcp = GoogleCloudPlatform(config['auth'],
                                  config['project'],
                                  config['scope'],
                                  logger)

        upload_agent_key(gcp, config)
        network = utils.get_gcp_resource_name(config['network'])
        response = gcp.create_network(network)
        gcp.wait_for_operation(response['name'], True)
        resource_register['network'] = network
        firewall = config['firewall']
        firewall['name'] = utils.get_firewall_rule_name(network, firewall)
        firewall['name'] = utils.get_gcp_resource_name(firewall['name'])
        response = gcp.create_firewall_rule(network, firewall)
        gcp.wait_for_operation(response['name'], True)
        resource_register['firewall'] = firewall['name']
        logger.info('Creating cloudify manager instance.')
        instance_name = utils.get_gcp_resource_name(config['name'])
        response = gcp.create_instance(
            instance_name=instance_name,
            agent_image=config['manager_image'],
            network=network,
            startup_script=config['startup_script'])
        gcp.wait_for_operation(response['name'])
        resource_register['instance'] = instance_name
        logger.info('Instance created. \n '
                    'It will take a minute or two for the instance '
                    'to complete work.')
    except Exception as e:
        logger.error(str(e))
        cleanup(resource_register, gcp)


def cleanup(resource_register, gcp):
    logger.info("Cleanup")
    if not resource_register:
        return
    firewall = resource_register.get('firewall_rule')
    network = resource_register.get('network')
    instance = resource_register.get('instance')
    if firewall:
        response = gcp.delete_firewall_rule(network, firewall)
        gcp.wait_for_operation(response['name'], True)
    if network:
        response = gcp.delete_network(network)
        gcp.wait_for_operation(response['name'], True)
    if instance:
        response = gcp.delete_instance(instance)
        gcp.wait_for_operation(response['name'])


def find_and_replace(file_name, replace):
    with open(file_name, 'r+') as f:
        script = f.read()
        for item in replace:
            script = script.replace(item, replace[item])
        f.seek(0)
        f.write(script)
        f.truncate()


def prepare_startup_script(config):
    with open(config['ssh_key_private'], 'r') as f:
        ssh_private = f.read()
    with open(config['ssh_key_public'], 'r') as f:
        ssh_public = f.read()
    with open(config['auth'], 'r') as f:
        auth_file = f.read()

    replace = {
        'USER=default': "USER={0}".format(config['agent_user']),
        'SSH_PRIVATE_KEY': ssh_private,
        'SSH_PUBLIC_KEY': ssh_public,
        'AUTH_FILE': auth_file
    }
    auth_file_location = config.get('auth_file_location')
    if auth_file_location:
        replace['AUTH_LOCATION=$HOME/auth'] = \
            'AUTH_LOCATION={0}'.format(auth_file_location)

    find_and_replace('startup-script.sh', replace)


def upload_agent_key(gcp, config):
    with open(config['ssh_key_public'], 'r') as f:
        ssh_public = f.read()
    response = gcp.update_project_ssh_keypair(config['agent_user'], ssh_public)
    gcp.wait_for_operation(response['name'], True)


def main():
    with open(CONFIG) as f:
        config = yaml.safe_load(f).get('config')
    prepare_startup_script(config)
    run(config)


if __name__ == '__main__':
    main()
