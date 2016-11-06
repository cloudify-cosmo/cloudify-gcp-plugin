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

import random
from os.path import basename

from cloudify import ctx
from cloudify.decorators import operation
from cloudify.exceptions import NonRecoverableError

from .. import utils
from .. import constants
from .keypair import KeyPair
from ..gcp import (
        GCPError,
        check_response,
        GoogleCloudPlatform,
        )


class Instance(GoogleCloudPlatform):
    ACCESS_CONFIG = 'External NAT'
    ACCESS_CONFIG_TYPE = 'ONE_TO_ONE_NAT'
    NETWORK_INTERFACE = 'nic0'
    STANDARD_MACHINE_TYPE = 'n1-standard-1'
    DEFAULT_SCOPES = ['https://www.googleapis.com/auth/devstorage.read_write',
                      'https://www.googleapis.com/auth/logging.write']

    def __init__(self,
                 config,
                 logger,
                 name,
                 additional_settings=None,
                 image=None,
                 disks=None,
                 machine_type=None,
                 startup_script=None,
                 external_ip=False,
                 tags=None,
                 scopes=None,
                 ssh_keys=None,
                 network=None,
                 subnetwork=None,
                 zone=None,
                 can_ip_forward=False,
                 ):
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
            utils.get_gcp_resource_name(name),
            additional_settings)
        self.image = image
        self.machine_type = machine_type
        self.startup_script = startup_script
        self.tags = tags + [self.name] if tags else [self.name]
        self.externalIP = external_ip
        self.disks = disks or []
        self.scopes = scopes or self.DEFAULT_SCOPES
        self.ssh_keys = ssh_keys or []
        self.zone = zone
        self.network = network
        self.subnetwork = subnetwork
        self.can_ip_forward = can_ip_forward

    @utils.async_operation(get=True)
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

        disk = ctx.instance.runtime_properties.get(constants.DISK)
        if disk:
            self.disks = [disk]
        if not self.disks and not self.image:
            raise NonRecoverableError("A disk image ID must be provided")

        return self.discovery.instances().insert(
            project=self.project,
            zone=basename(self.zone),
            body=self.to_dict()).execute()

    @utils.async_operation()
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
            zone=basename(self.zone),
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
        self.tags = tag_dict.get('items', [])
        self.tags.extend(tags)
        self.tags = list(set(self.tags))
        fingerprint = tag_dict['fingerprint']
        return self.discovery.instances().setTags(
            project=self.project,
            zone=basename(self.zone),
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
        tag_dict = self.get()['tags']
        self.tags = tag_dict.get('items', [])

        self.tags = [tag for tag in self.tags if tag not in tags]
        fingerprint = tag_dict['fingerprint']
        return self.discovery.instances().setTags(
            project=self.project,
            zone=basename(self.zone),
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
            zone=basename(self.zone)).execute()

    @check_response
    def add_access_config(self, ip_address=''):
        """
        Set GCP instance external IP.
        Zone operation.

        :param ip_address: ip address of external IP, if not set new IP
        address assigned
        :return: REST response with operation responsible for the instance
        external IP setting process and its status
        """
        self.logger.info('Add external IP to instance {0}'.format(self.name))

        body = {'kind': 'compute#accessConfig',
                'name': self.ACCESS_CONFIG,
                'type': self.ACCESS_CONFIG_TYPE}
        if ip_address:
            body['natIP'] = ip_address

        return self.discovery.instances().addAccessConfig(
            project=self.project,
            instance=self.name,
            zone=basename(self.zone),
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
            zone=basename(self.zone),
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
            zone=basename(self.zone),
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
            zone=basename(self.zone),
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
            zone=basename(self.zone)).execute()

    def to_dict(self):
        def add_key_value_to_metadata(key, value, body):
            ctx.logger.info('Adding {} to metadata'.format(key))
            body['metadata']['items'].append({'key': key, 'value': value})

        network = {'network': 'global/networks/default'}
        if self.network and self.network != 'default':
            network['network'] = self.network
        if self.subnetwork:
            network['subnetwork'] = self.subnetwork

        body = {
            'name': self.name,
            'description': 'Cloudify generated instance',
            'canIpForward': self.can_ip_forward,
            'tags': {'items': list(set(self.tags))},
            'machineType': 'zones/{0}/machineTypes/{1}'.format(
                basename(self.zone),
                self.machine_type),
            'networkInterfaces': [network],
            'serviceAccounts': [
                {'email': 'default',
                 'scopes': self.scopes
                 }],
            'metadata': {
                'items': [{'key': 'bucket', 'value': self.project}]
            }
        }
        self.body.update(body)
        ssh_keys_str = '\n'.join(self.ssh_keys)
        add_key_value_to_metadata(KeyPair.KEY_VALUE,
                                  ssh_keys_str,
                                  self.body)
        if self.startup_script:
            add_key_value_to_metadata('startup-script',
                                      self.startup_script,
                                      self.body)

        if not self.disks:
            self.disks = [{'boot': True,
                           'autoDelete': True,
                           'initializeParams': {
                               'sourceImage': self.image
                           }}]
        self.body['disks'] = self.disks

        if self.externalIP:
            # GCP Instances only support a single networkInterface, with a
            # single accessConfig, so there's no need to look them up in a
            # sophisiticated way.
            self.body['networkInterfaces'][0]['accessConfigs'] = [{
                'type': self.ACCESS_CONFIG_TYPE,
                'name': self.ACCESS_CONFIG,
                }]

        return self.body


@operation
@utils.throw_cloudify_exceptions
def create(instance_type,
           image_id,
           name,
           external_ip,
           startup_script,
           scopes,
           tags,
           zone=None,
           can_ip_forward=False,
           additional_settings=None,
           **kwargs):
    props = ctx.instance.runtime_properties
    gcp_config = utils.get_gcp_config()

    script = ''

    if startup_script:
        if startup_script.get('type') == 'file':
            script = ctx.get_resource(startup_script.get('script'))
        elif startup_script.get('type') == 'string':
            script = startup_script.get('script')
        else:
            raise NonRecoverableError(
                'invalid script type: {}'.format(startup_script.get('type')))
    ctx.logger.info('The script is {0}'.format(str(startup_script)))

    ssh_keys = get_ssh_keys()

    network, subnetwork = utils.get_net_and_subnet(ctx)

    if zone:
        zone = props['zone'] = utils.get_gcp_resource_name(zone)
    else:
        if props.get('zone', False):
            zone = props['zone']
        elif subnetwork:
            zone = props['zone'] = random.choice(constants.REGION_ZONES_FULL[
                basename(utils.get_network_node(ctx)
                         .instance.runtime_properties['region'])])
        else:
            zone = props['zone'] = utils.get_gcp_resource_name(
                    gcp_config['zone'])

    disks = [
            disk.target.instance.runtime_properties[constants.DISK]
            for disk
            in utils.get_relationships(
                ctx,
                filter_resource_types='compute#disk'
                )
            ]
    # There must be exactly one boot disk and that disk must be first in the
    # `disks` list.
    disks.sort(key=lambda disk: disk['boot'], reverse=True)
    boot_disks = [x for x in disks if x['boot']]
    if len(boot_disks) > 1:
        raise NonRecoverableError(
                'Only one disk per Instance may be a boot disk. '
                'Disks: {}'.format(boot_disks)
                )

    instance_name = utils.get_final_resource_name(name)
    instance = Instance(
            gcp_config,
            ctx.logger,
            name=instance_name,
            disks=disks,
            image=image_id,
            machine_type=instance_type,
            external_ip=external_ip,
            startup_script=script,
            scopes=scopes,
            tags=tags,
            ssh_keys=ssh_keys,
            network=network,
            subnetwork=subnetwork,
            zone=zone,
            can_ip_forward=can_ip_forward,
            additional_settings=additional_settings,
            )

    utils.create(instance)


@operation
@utils.throw_cloudify_exceptions
def start(**kwargs):
    gcp_config = utils.get_gcp_config()
    props = ctx.instance.runtime_properties
    instance = Instance(gcp_config,
                        ctx.logger,
                        name=props['name'],
                        zone=basename(props['zone']),
                        )
    set_ip(instance)


@operation
@utils.throw_cloudify_exceptions
def delete(name, zone, **kwargs):
    gcp_config = utils.get_gcp_config()
    props = ctx.instance.runtime_properties

    if not zone:
        zone = props['zone']
    if not name:
        name = props['name']

    if name:
        instance = Instance(gcp_config,
                            ctx.logger,
                            name=name,
                            zone=zone,
                            )
        props.pop(constants.DISK, None)

        utils.delete_if_not_external(instance)


@operation
@utils.throw_cloudify_exceptions
def add_instance_tag(instance_name, zone, tag, **kwargs):
    config = utils.get_gcp_config()
    config['network'] = utils.get_gcp_resource_name(config['network'])
    instance = Instance(config,
                        ctx.logger,
                        name=instance_name,
                        zone=zone,
                        )
    instance.set_tags([utils.get_gcp_resource_name(t) for t in tag])


@operation
@utils.throw_cloudify_exceptions
def remove_instance_tag(instance_name, zone, tag, **kwargs):
    config = utils.get_gcp_config()
    if instance_name:
        config['network'] = utils.get_gcp_resource_name(config['network'])
        instance = Instance(config,
                            ctx.logger,
                            name=instance_name,
                            zone=zone,
                            )
        instance.remove_tags([utils.get_gcp_resource_name(t) for t in tag])


@operation
@utils.throw_cloudify_exceptions
def add_external_ip(instance_name, zone, **kwargs):
    gcp_config = utils.get_gcp_config()
    # check if the instance has no external ips, only one is supported so far
    gcp_config['network'] = utils.get_gcp_resource_name(gcp_config['network'])
    ip_node = ctx.target.node

    # Might be overridden by either `use_external_resource` or a connected
    # Address
    ip_address = ''

    instance = Instance(
            gcp_config,
            ctx.logger,
            name=instance_name,
            zone=zone,
            )

    if ip_node.properties[constants.USE_EXTERNAL_RESOURCE]:
        ip_address = (
                ip_node.properties.get('ip_address') or
                ctx.target.instance.runtime_properties.get(constants.IP)
                )
        if not ip_address:
            raise GCPError('{} is set, but ip_address is not set'
                           .format(constants.USE_EXTERNAL_RESOURCE))
    elif ip_node.type == 'cloudify.gcp.nodes.Address':
        ip_address = ctx.target.instance.runtime_properties['address']
    elif ip_node.type != 'cloudify.gcp.nodes.ExternalIP':
        raise NonRecoverableError(
                'Incorrect node type ({}) used as Instance external IP'.format(
                    ip_node.type,
                    ))

    # If `ip_address` is still '' when we get here then the connected IP node
    # must be an ExternalIP, which means we should add the accessConfig
    # *without* a specified IP. The API will produce one for us in this case.

    instance.add_access_config(ip_address)
    set_ip(instance, relationship=True)


@operation
@utils.throw_cloudify_exceptions
def add_ssh_key(**kwargs):
    key = ctx.target.instance.runtime_properties[constants.PUBLIC_KEY]
    user = ctx.target.instance.runtime_properties[constants.USER]
    key_user_string = utils.get_key_user_string(user, key)
    properties = ctx.source.instance.runtime_properties

    instance_keys = properties.get(constants.SSH_KEYS, [])
    instance_keys.append(key_user_string)
    properties[constants.SSH_KEYS] = instance_keys
    ctx.logger.info('Adding key: {0}'.format(key_user_string))


@operation
@utils.throw_cloudify_exceptions
def remove_external_ip(instance_name, zone, **kwargs):
    if instance_name:
        gcp_config = utils.get_gcp_config()
        gcp_config['network'] = utils.get_gcp_resource_name(
                gcp_config['network'])
        instance = Instance(gcp_config,
                            ctx.logger,
                            name=instance_name,
                            zone=zone,
                            )
        instance.delete_access_config()


@operation
@utils.throw_cloudify_exceptions
def attach_disk(instance_name, zone, disk, **kwargs):
    gcp_config = utils.get_gcp_config()
    instance = Instance(gcp_config,
                        ctx.logger,
                        name=instance_name,
                        zone=zone,
                        )
    instance.attach_disk(disk)


@operation
@utils.throw_cloudify_exceptions
def detach_disk(instance_name, zone, disk_name, **kwargs):
    gcp_config = utils.get_gcp_config()
    instance = Instance(gcp_config,
                        ctx.logger,
                        name=instance_name,
                        zone=zone,
                        )
    instance.detach_disk(disk_name)


@operation
@utils.throw_cloudify_exceptions
def contained_in(**kwargs):
    key = ctx.target.instance.runtime_properties[constants.SSH_KEYS]
    ctx.source.instance.runtime_properties[constants.SSH_KEYS] = key
    ctx.logger.info('Copied ssh keys to the node')


def set_ip(instance, relationship=False):
    if relationship:
        props = ctx.source.instance.runtime_properties
    else:
        props = ctx.instance.runtime_properties

    instances = instance.list()
    item = utils.get_item_from_gcp_response('name',
                                            instance.name,
                                            instances)

    try:
        if relationship or ctx.node.properties['external_ip']:
            props.update(item)
            props['ip'] = item[
                    'networkInterfaces'][0]['accessConfigs'][0]['natIP']
        else:
            props['ip'] = item['networkInterfaces'][0]['networkIP']
        # only with one default network interface
    except (TypeError, KeyError):
        ctx.operation.retry(
                'The instance has not yet created network interface', 10)


def get_ssh_keys():
    instance_keys = ctx.instance.runtime_properties.get(constants.SSH_KEYS, [])
    install = ctx.node.properties['install_agent']
    # properties['install_agent'] defaults to '', but that means true!
    agent_config = ctx.node.properties.get('agent_config', {})
    if not any([
            agent_config.get('install_method') == 'none',
            install is False,
            ]):
        agent_key = utils.get_agent_ssh_key_string()
        instance_keys.append(agent_key)
    return list(set(instance_keys))


def validate_contained_in_network(**kwargs):
    rels = utils.get_relationships(
            ctx,
            filter_relationships='cloudify.gcp.relationships.'
                                 'instance_contained_in_network',
            filter_nodes=[
                'cloudify.gcp.nodes.Network',
                'cloudify.gcp.nodes.SubNetwork',
                ],
            )
    if len(rels) > 1:
        raise NonRecoverableError(
                'Instances may only be contained in 1 Network or SubNetwork')
    elif len(rels) == 1:
        network = rels[0].target
        if (network.node.type == 'cloudify.gcp.nodes.Network' and
                not network.node.properties['auto_subnets']):
            raise NonRecoverableError(
                    'It is invalid to connect an instance directly to a '
                    'network with custom Subtneworks (i.e. `auto_subnets` '
                    'disabled')
