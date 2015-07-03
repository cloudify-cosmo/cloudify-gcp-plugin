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
from plugin.gcp import utils
from plugin.gcp.service import GoogleCloudPlatform
from plugin.gcp.service import GCPError


class Instance(GoogleCloudPlatform):
    ACCESS_CONFIG = 'External NAT'
    ACCESS_CONFIG_TYPE = 'ONE_TO_ONE_NAT'
    NETWORK_INTERFACE = 'nic0'
    STANDARD_MACHINE_TYPE = 'n1-standard-1'

    def __init__(self,
                 config,
                 logger,
                 name,
                 image=None,
                 machine_type=None,
                 startup_script=None,
                 external_ip=False,
                 tags=None):
        """
        Create Instance object

        :param config: gcp auth file
        :param logger: logger object
        :param name: name of the instance
        :param image: image id in Google Cloud Platform
        :param machine_type: machine type on GCP, default None
        :param startup_script: shell script text to be run on instance startup,
        default None
        :param external_ip: boolean external ip indicator, default False
        :param tags: tags for the instance, default []
        """
        super(Instance, self).__init__(
            config,
            logger,
            utils.get_gcp_resource_name(name))
        self.image = image
        self.machine_type = machine_type
        self.network = config['network']
        self.startup_script = startup_script
        self.tags = tags.append(self.name) if tags else [self.name]
        self.externalIP = external_ip
        self.disks = []

    def create(self):
        """
        Create GCP VM instance with given parameters.
        Zone operation.

        :return: REST response with operation responsible for the instance
        creation process and its status
        :raise: GCPError if there is any problem with startup script file:
        e.g. the file is not under the given path or it has wrong permissions
        """
        self.logger.info(
            'Create instance {0}, zone {1}, project {2}'.format(
                self.name,
                self.zone,
                self.project))

        body = self.to_dict()
        if self.startup_script is not None:
            try:
                with open(self.startup_script, 'r') as script:
                    item = {
                        'key': 'startup-script',
                        'value': script.read()
                    }
                    body['metadata']['items'].append(item)
            except IOError as e:
                self.logger.error(str(e))
                raise GCPError(str(e))

        return self.discovery.instances().insert(
            project=self.project,
            zone=self.zone,
            body=body).execute()

    def delete(self):
        """
        Delete GCP instance.
        Zone operation.

        :return: REST response with operation responsible for the instance
        deletion process and its status
        """
        self.logger.info('Delete instance {0}'.format(self.name))
        return self.discovery.instances().delete(
            project=self.project,
            zone=self.zone,
            instance=self.name).execute()

    def set_tags(self, tags):
        """
        Set GCP instance tags.
        Zone operation.

        :return: REST response with operation responsible for the instance
        tag setting process and its status
        """
        # each tag should be RFC1035 compliant
        self.logger.info(
            'Set tags {0} to instance {1}'.format(str(self.tags), self.name))

        self.tags.extend(tags)
        self.tags = list(set(self.tags))
        fingerprint = self.get()['tags']['fingerprint']
        return self.discovery.instances().setTags(
            project=self.project,
            zone=self.zone,
            instance=self.name,
            body={'items': self.tags, 'fingerprint': fingerprint}).execute()

    def remove_tags(self, tags):
        """
        Remove GCP instance tags.
        Zone operation.

        :return: REST response with operation responsible for the instance
        tag removal process and its status
        """
        # each tag should be RFC1035 compliant
        self.logger.info(
            'Remove tags {0} from instance {1}'.format(
                str(self.tags),
                self.name))

        self.tags = [tag for tag in self.tags if tag not in tags]
        fingerprint = self.get()['tags']['fingerprint']
        return self.discovery.instances().setTags(
            project=self.project,
            zone=self.zone,
            instance=self.name,
            body={'items': self.tags, 'fingerprint': fingerprint}).execute()

    def get(self):
        """
        Get GCP instance details.
        """
        self.logger.info('Get instance {0} details'.format(self.name))

        return self.discovery.instances().get(
            instance=self.name,
            project=self.project,
            zone=self.zone).execute()

    def add_access_config(self):
        """
        Set GCP instance external IP.
        Zone operation.

        :return: REST response with operation responsible for the instance
        external IP setting process and its status
        """
        self.logger.info('Add external IP to instance {0}'.format(self.name))

        body = {'kind': 'compute#accessConfig',
                'name': self.ACCESS_CONFIG,
                'type': self.ACCESS_CONFIG_TYPE}
        return self.discovery.instances().addAccessConfig(
            project=self.project,
            instance=self.name,
            zone=self.zone,
            networkInterface=self.NETWORK_INTERFACE,
            body=body).execute()

    def delete_access_config(self):
        """
        Set GCP instance tags.
        Zone operation.

        :return: REST response with operation responsible for the instance
        external ip removing process and its status
        """
        self.logger.info(
            'Remove external IP from instance {0}'.format(self.name))

        return self.discovery.instances().deleteAccessConfig(
            project=self.project,
            instance=self.name,
            zone=self.zone,
            accessConfig=self.ACCESS_CONFIG,
            networkInterface=self.NETWORK_INTERFACE).execute()

    def attach_disk(self, disk):
        return self.discovery.instances().attachDisk(
            project=self.project,
            zone=self.zone,
            instance=self.name,
            body=disk).execute()

    def detach_disk(self, disk_name):
        return self.discovery.instances().detachDisk(
            project=self.project,
            zone=self.zone,
            instance=self.name,
            deviceName=disk_name).execute()

    def list(self):
        """
        List GCP instances.
        Zone operation.

        :return: REST response with a list of instances and its details
        """
        self.logger.info('List instances in project {0}'.format(self.project))

        return self.discovery.instances().list(
            project=self.project,
            zone=self.zone).execute()

    def to_dict(self):
        body = {
            'name': self.name,
            'description': 'Cloudify generated instance',
            'tags': {'items': list(set(self.tags))},
            'machineType': 'zones/{0}/machineTypes/{1}'.format(
                self.zone,
                self.machine_type),
            'networkInterfaces': [
                {'network': 'global/networks/{0}'.format(self.network)}],
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
        if not self.disks:
            self.disks = [{'boot': True,
                           'autoDelete': True,
                           'initializeParams': {
                               'sourceImage': self.image
                           }}]
        body['disks'] = self.disks

        if self.externalIP:
            for item in body['networkInterfaces']:
                if item['name'] == self.ACCESS_CONFIG:
                    item['accessConfigs'] = [{'type': self.ACCESS_CONFIG_TYPE,
                                              'name': self.ACCESS_CONFIG}]
        return body
