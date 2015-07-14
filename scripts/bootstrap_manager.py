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
import Queue

import yaml

from plugin.gcp.service import GoogleCloudPlatform
from plugin.gcp import resources
from plugin.gcp import utils
from plugin import tags

CONFIG = 'inputs_gcp.yaml'
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
logger = logging.getLogger()


def run(config, network_conf, firewall_conf):
    resource_register = Queue.LifoQueue()
    try:
        upload_agent_key(config)
        network = resources.Network(config, logger, network_conf)
        network.create()
        resource_register.put(network)
        firewall = resources.FirewallRule(config,
                                          logger,
                                          firewall_conf,
                                          network.name)
        firewall.create()
        resource_register.put(firewall)

        logger.info('Creating cloudify manager instance.')
        instance_name = utils.get_gcp_resource_name(config['manager_name'])
        instance = resources.Instance(
            config,
            logger,
            instance_name=instance_name,
            image=config['image'],
            startup_script=config['startup_script'],
            tags=[tags.MANAGER_TAG])
        instance.create()
        resource_register.put(instance)
        logger.info('Instance created. \n '
                    'It will take a minute or two for the instance '
                    'to complete work.')
    except Exception as e:
        logger.error(str(e))
        cleanup(resource_register)


def cleanup(resource_register):
    logger.info("Cleanup")
    while not resource_register.empty():
        resource_register.get().delete()


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
        replace['AUTH_LOCATION=/home/$USER/auth'] = \
            'AUTH_LOCATION={0}'.format(auth_file_location)

    find_and_replace(config['startup_script'], replace)


def upload_agent_key(config):
    with open(config['ssh_key_public'], 'r') as f:
        ssh_public = f.read()
    gcp = GoogleCloudPlatform(config, logger)
    gcp.update_project_ssh_keypair(config['agent_user'], ssh_public)


def main():
    with open(CONFIG) as f:
        inputs = yaml.safe_load(f)
    config = inputs.get('config')
    prepare_startup_script(config)
    run(config, inputs.get('network'), inputs.get('firewall'))


if __name__ == '__main__':
    main()
