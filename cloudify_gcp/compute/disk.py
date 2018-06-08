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
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from cloudify import ctx
from cloudify.decorators import operation
from cloudify.exceptions import NonRecoverableError

from .. import constants
from .. import utils
from cloudify_gcp.gcp import GoogleCloudPlatform
from cloudify_gcp.gcp import check_response


class Snapshot(GoogleCloudPlatform):
    def __init__(self,
                 config,
                 logger,
                 name,
                 description=None,
                 additional_settings=None):
        super(Snapshot, self).__init__(config, logger, name, additional_settings)
        self.description = description

    def to_dict(self):
        self.body.update({
            'description': 'Cloudify generated snapshot',
            'name': self.name
        })
        return self.body

    @check_response
    def get(self):
        return self.discovery.snapshots().get(
            project=self.project,
            snapshot=self.name).execute()

    @utils.async_operation()
    @check_response
    def delete(self):
        return self.discovery.snapshots().delete(
            project=self.project,
            snapshot=self.name).execute()

    @utils.async_operation()
    @check_response
    def create(self, disk_name):
        return self.discovery.disks().createSnapshot(
            project=self.project,
            zone=self.zone,
            disk=disk_name,
            body={
                "name": self.name,
                "description": self.description
            }).execute()


class Disk(GoogleCloudPlatform):
    def __init__(self,
                 config,
                 logger,
                 name,
                 boot=False,
                 additional_settings=None,
                 image=None,
                 size_gb=None):
        super(Disk, self).__init__(config, logger, name, additional_settings)
        self.image = image
        self.sizeGb = size_gb
        self.boot = boot

    def to_dict(self):
        self.body.update({
            'description': 'Cloudify generated disk',
            'name': self.name
        })
        if self.image:
            self.body['sourceImage'] = self.image
        if self.sizeGb:
            self.body['sizeGb'] = self.sizeGb
        return self.body

    def disk_to_insert_instance_dict(self, mount_name):
        disk_info = self.get()
        body = {
            'deviceName': mount_name,
            'boot': self.boot,
            'mode': 'READ_WRITE',
            'autoDelete': False,
            'source': disk_info['selfLink']
        }
        return body

    @check_response
    def get(self):
        return self.discovery.disks().get(
            project=self.project,
            zone=self.zone,
            disk=self.name).execute()

    @check_response
    def list(self):
        return self.discovery.disks().list(
            project=self.project,
            zone=self.zone).execute()

    @utils.sync_operation
    @check_response
    def create(self):
        return self.discovery.disks().insert(
            project=self.project,
            zone=self.zone,
            body=self.to_dict()).execute()

    @utils.async_operation()
    @check_response
    def delete(self):
        return self.discovery.disks().delete(
            project=self.project,
            zone=self.zone,
            disk=self.name).execute()


@operation
@utils.throw_cloudify_exceptions
def create(image, name, size, boot, additional_settings, **kwargs):
    name = utils.get_final_resource_name(name)
    gcp_config = utils.get_gcp_config()
    disk = Disk(gcp_config,
                ctx.logger,
                image=image,
                name=name,
                size_gb=size,
                boot=boot,
                additional_settings=additional_settings)
    utils.create(disk)
    ctx.instance.runtime_properties.update(disk.get())
    ctx.instance.runtime_properties[constants.DISK] = \
        disk.disk_to_insert_instance_dict(name)


@operation
@utils.retry_on_failure('Retrying deleting disk')
@utils.throw_cloudify_exceptions
def delete(**kwargs):
    gcp_config = utils.get_gcp_config()
    name = ctx.instance.runtime_properties.get('name')
    if name:
        disk = Disk(gcp_config,
                    ctx.logger,
                    name=name)
        utils.delete_if_not_external(disk)


def _get_backupname(kwargs):
    if not kwargs.get("snapshot_name"):
        raise NonRecoverableError(
            'Backup name must be provided.'
        )
    return utils.get_gcp_resource_name(kwargs["snapshot_name"])


@operation
@utils.retry_on_failure('Retrying create dish snapshot')
@utils.throw_cloudify_exceptions
def snapshot_create(**kwargs):
    snapshot_type = kwargs.get('snapshot_type')
    snapshot_name = _get_backupname(kwargs)
    if not kwargs.get("snapshot_incremental"):
        ctx.logger.info("Create backup for VM is unsupported.")
        return

    gcp_config = utils.get_gcp_config()
    name = ctx.instance.runtime_properties.get('name')
    if name:
        snapshot = Snapshot(gcp_config,
                    ctx.logger,
                    name=snapshot_name,
                    description=snapshot_type)
        snapshot.create(disk_name=name)


@operation
@utils.retry_on_failure('Retrying deleting snapshot')
@utils.throw_cloudify_exceptions
def snapshot_delete(**kwargs):
    snapshot_name = _get_backupname(kwargs)
    if not kwargs.get("snapshot_incremental"):
        ctx.logger.info("Delete backup for VM is unsupported.")
        return

    gcp_config = utils.get_gcp_config()
    snapshot = Snapshot(gcp_config,
                        ctx.logger,
                        name=snapshot_name)
    snapshot.delete()


@operation
@utils.throw_cloudify_exceptions
def add_boot_disk(**kwargs):
    disk_body = ctx.target.instance.runtime_properties[constants.DISK]
    disk_body['boot'] = True
    ctx.source.instance.runtime_properties[constants.DISK] = disk_body
