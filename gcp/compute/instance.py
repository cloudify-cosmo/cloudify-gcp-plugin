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
from cloudify import ctx
from cloudify.decorators import operation

from gcp.compute import constants
from gcp.compute import utils
from gcp.compute.keypair import KeyPair
from gcp.gcp import GoogleCloudPlatform
from gcp.gcp import check_response
from gcp.gcp import GCPError


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

    def get_instance_ssh_keys(self):
        agent_key = utils.get_agent_ssh_key_string()
        other_keys = ctx.instance.runtime_properties.get(constants.SSHKEY)
        return other_keys + '\n' + agent_key if other_keys else agent_key

    @check_response
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

    @check_response
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

    @check_response
    def set_tags(self, tags):
        """
        Set GCP instance tags.
        Zone operation.

        :return: REST response with operation responsible for the instance
        tag setting process and its status
        """
        # each tag should be RFC1035 compliant
        self.logger.info(
            'Set tags {0} to instance {1}'.format(str(tags), self.name))
        tag_dict = self.get()['tags']
        self.tags = tag_dict['items']
        self.tags = self.tags.extend(tags)
        self.tags = list(set(self.tags))
        fingerprint = tag_dict['fingerprint']
        return self.discovery.instances().setTags(
            project=self.project,
            zone=self.zone,
            instance=self.name,
            body={'items': self.tags, 'fingerprint': fingerprint}).execute()

    @check_response
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

    @check_response
    def get(self):
        """
        Get GCP instance details.

        :return: REST response with operation responsible for the instance
        details retrieval
        """
        self.logger.info('Get instance {0} details'.format(self.name))

        return self.discovery.instances().get(
            instance=self.name,
            project=self.project,
            zone=self.zone).execute()

    @check_response
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

    @check_response
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

    @check_response
    def attach_disk(self, disk):
        """
        Attach disk to the instance.

        :param disk: disk structure to be attached to the instance
        :return:
        """
        return self.discovery.instances().attachDisk(
            project=self.project,
            zone=self.zone,
            instance=self.name,
            body=disk).execute()

    @check_response
    def detach_disk(self, disk_name):
        """
        Detach disk identified by the name from the instance.

        :param disk_name: name of the disk to be detached
        :return:
        """
        return self.discovery.instances().detachDisk(
            project=self.project,
            zone=self.zone,
            instance=self.name,
            deviceName=disk_name).execute()

    @check_response
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
                    {'key': 'bucket', 'value': self.project},
                    {KeyPair.KEY_NAME: KeyPair.KEY_VALUE, 'value': self.get_instance_ssh_keys()}]
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
        ctx.logger.info('Instance dict: {0}'.format(str(body)))
        return body


@operation
@utils.throw_cloudify_exceptions
def create(instance_type, image_id, properties, name, **kwargs):
    gcp_config = utils.get_gcp_config()
    gcp_config['network'] = utils.get_gcp_resource_name(gcp_config['network'])
    script = properties.get('startup_script')
    if script:
        script = ctx.download_resource(script)
    instance_name = get_instance_name(name)
    instance = Instance(gcp_config,
                        ctx.logger,
                        name=instance_name,
                        image=image_id,
                        machine_type=instance_type,
                        external_ip=properties.get('externalIP', False),
                        startup_script=script)
    ctx.instance.runtime_properties[constants.NAME] = instance.name
    if ctx.node.properties['install_agent']:
        add_to_security_groups(instance)
    disk = ctx.instance.runtime_properties.get(constants.DISK)
    if disk:
        instance.disks = [disk]
    create_instance(instance)
    set_ip(instance)


def get_instance_name(name):
    if utils.should_use_external_resource():
        return utils.assure_resource_id_correct()
    else:
        return name or utils.get_gcp_resource_name(ctx.instance.id)


@utils.create_resource
def create_instance(instance):
    instance.create()


@operation
@utils.retry_on_failure('Retrying deleting instance')
@utils.throw_cloudify_exceptions
def delete(**kwargs):
    gcp_config = utils.get_gcp_config()
    name = ctx.instance.runtime_properties.get(constants.NAME, None)
    if not name:
        return
    instance = Instance(gcp_config,
                        ctx.logger,
                        name=name)
    delete_instance(instance)

    ctx.instance.runtime_properties.pop(constants.DISK, None)
    ctx.instance.runtime_properties.pop(constants.NAME, None)


def delete_instance(instance):
    if not utils.should_use_external_resource():
        instance.delete()


@operation
@utils.throw_cloudify_exceptions
def add_instance_tag(instance_name, tag, **kwargs):
    if not tag:
        return
    gcp_config = utils.get_gcp_config()
    gcp_config['network'] = utils.get_gcp_resource_name(gcp_config['network'])
    instance = Instance(gcp_config,
                        ctx.logger,
                        name=instance_name)
    instance.set_tags([utils.get_gcp_resource_name(t) for t in tag])


@operation
@utils.throw_cloudify_exceptions
def remove_instance_tag(instance_name, tag, **kwargs):
    gcp_config = utils.get_gcp_config()
    if not instance_name:
        return
    gcp_config['network'] = utils.get_gcp_resource_name(gcp_config['network'])
    instance = Instance(gcp_config,
                        ctx.logger,
                        name=instance_name)
    instance.remove_tags([utils.get_gcp_resource_name(t) for t in tag])


@operation
@utils.throw_cloudify_exceptions
def add_external_ip(instance_name, **kwargs):
    gcp_config = utils.get_gcp_config()
    # check if the instance has no external ips, only one is supported so far
    gcp_config['network'] = utils.get_gcp_resource_name(gcp_config['network'])
    instance = Instance(gcp_config,
                        ctx.logger,
                        name=instance_name)
    instance.add_access_config()
    set_ip(instance, relationship=True)


@operation
@utils.throw_cloudify_exceptions
def add_ssh_key(**kwargs):
    key = ctx.target.instance.runtime_properties[constants.PUBLIC_KEY]
    user = ctx.target.instance.runtime_properties[constants.USER]
    key_user_string = utils.get_key_user_string(user, key + ' ' + user)
    previous_keys = ctx.source.instance.runtime_properties.get(constants.SSHKEY)
    ctx.source.instance.runtime_properties[constants.SSHKEY] = \
        previous_keys + '\n' + key_user_string if previous_keys else key_user_string
    ctx.logger.info('sshKeys are: {0}'
                    .format(ctx.source.instance.runtime_properties[constants.SSHKEY]))


@operation
def contained_in(**kwargs):
    key = ctx.target.instance.runtime_properties[constants.SSHKEY]
    ctx.source.instance.runtime_properties[constants.SSHKEY] = key
    ctx.logger.info('Copied ssh keys to the node')


@operation
@utils.throw_cloudify_exceptions
def remove_external_ip(instance_name, **kwargs):
    if not instance_name:
        return
    gcp_config = utils.get_gcp_config()
    gcp_config['network'] = utils.get_gcp_resource_name(gcp_config['network'])
    instance = Instance(gcp_config,
                        ctx.logger,
                        name=instance_name)
    instance.delete_access_config()


@operation
@utils.throw_cloudify_exceptions
def attach_disk(instance_name, disk, **kwargs):
    gcp_config = utils.get_gcp_config()
    instance = Instance(gcp_config,
                        ctx.logger,
                        name=instance_name)
    instance.attach_disk(disk)


@operation
@utils.throw_cloudify_exceptions
def detach_disk(instance_name, disk_name, **kwargs):
    gcp_config = utils.get_gcp_config()
    instance = Instance(gcp_config,
                        ctx.logger,
                        name=instance_name)
    instance.detach_disk(disk_name)


def set_ip(instance, relationship=False):
    instances = instance.list()
    item = utils.get_item_from_gcp_response('name',
                                            instance.name,
                                            instances)
    try:
        if relationship:
            ctx.target.instance.runtime_properties['gcp_resource_id'] = \
                item['networkInterfaces'][0]['accessConfigs'][0]['natIP']
        else:
            ctx.instance.runtime_properties['ip'] = \
                item['networkInterfaces'][0]['networkIP']
        # only with one default network interface
    except (TypeError, KeyError):
        ctx.operation.retry('The instance has not yet created network interface', 10)


def add_to_security_groups(instance):
    provider_config = utils.get_manager_provider_config()
    instance.tags.extend(
        provider_config[constants.AGENTS_SECURITY_GROUP]
        .get(constants.TARGET_TAGS))
