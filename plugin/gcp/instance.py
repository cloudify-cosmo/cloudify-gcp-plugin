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
from plugin.gcp.service import blocking


class Instance(GoogleCloudPlatform):
    ACCESS_CONFIG = 'External NAT'
    ACCESS_CONFIG_TYPE = 'ONE_TO_ONE_NAT'
    NETWORK_INTERFACE = 'nic0'
    STANDARD_MACHINE_TYPE = 'n1-standard-1'

    def __init__(self,
                 config,
                 logger,
                 instance_name,
                 image=None,
                 machine_type=None,
                 startup_script=None,
                 external_ip=False,
                 tags=[]):
        """
        Create Instance object

        :param config: gcp auth file
        :param logger: logger object
        :param instance_name: name of the instance
        :param image: image id in Google Cloud Platform
        :param machine_type: machine type on GCP, default None
        :param startup_script: shell script text to be run on instance startup,
        default None
        :param external_ip: boolean external ip indicator, default False
        :param tags: tags for the instance, default []
        """
        super(Instance, self).__init__(config, logger)
        self.project = config['project']
        self.zone = config['zone']
        self.name = utils.get_gcp_resource_name(instance_name)
        self.image = image
        self.machine_type = machine_type \
            if machine_type else self.STANDARD_MACHINE_TYPE
        self.network = config['network']
        self.startup_script = startup_script
        self.tags = tags
        self.externalIP = external_ip

    @blocking(True)
    def create(self):
        """
        Create GCP VM instance with given parameters.
        Zone operation.

        :return: REST response with operation responsible for the instance
        creation process and its status
        :raise: GCPError if there is any problem with startup script file:
        e.g. the file is not under the given path or it has wrong permissions
        """
        self.logger.info('Create instance')
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
        """
        Set GCP instance tags.
        Zone operation.

        :return: REST response with operation responsible for the instance
        tag setting process and its status
        """
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

    @blocking(True)
    def remove_tags(self, tags):
        """
        Remove GCP instance tags.
        Zone operation.

        :return: REST response with operation responsible for the instance
        tag removal process and its status
        """
        # each tag should be RFC1035 compliant
        self.logger.info('Remove tags')
        self.tags = [tag for tag in self.tags if tag not in tags]
        fingerprint = self.get()["tags"]["fingerprint"]
        return self.compute.instances().setTags(
            project=self.project,
            zone=self.zone,
            instance=self.name,
            body={"items": self.tags, "fingerprint": fingerprint}).execute()

    def get(self):
        """
        Get GCP instance details.
        """
        self.logger.info("Get instance details")
        return self.compute.instances().get(
            instance=self.name,
            project=self.project,
            zone=self.zone).execute()

    @blocking(True)
    def add_access_config(self):
        """
        Set GCP instance external IP.
        Zone operation.

        :return: REST response with operation responsible for the instance
        external IP setting process and its status
        """
        body = {"kind": "compute#accessConfig",
                "name": self.ACCESS_CONFIG,
                "type": self.ACCESS_CONFIG_TYPE}
        return self.compute.instances().addAccessConfig(
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
        tag setting process and its status
        """
        return self.compute.instances().deleteAccessConfig(
            project=self.project,
            instance=self.name,
            zone=self.zone,
            accessConfig=self.ACCESS_CONFIG,
            networkInterface=self.NETWORK_INTERFACE).execute()

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
        if self.tags:
            body['tags'] = {"items": self.tags}
        if self.externalIP:
            for item in body['networkInterfaces']:
                if item['name'] == self.ACCESS_CONFIG:
                    item['accessConfigs'] = [{'type': 'ONE_TO_ONE_NAT',
                                              'name': 'External NAT'}]
        return body
