# #######
# Copyright (c) 2014-2020 Cloudify Platform Ltd. All rights reserved
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
        super(Snapshot, self).__init__(config, logger, name,
                                       additional_settings)
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


def _get_backupname(kwargs):
    if not kwargs.get("snapshot_name"):
        raise NonRecoverableError(
            'Backup name must be provided.'
        )
    return utils.get_gcp_resource_name(kwargs["snapshot_name"])


@operation(resumable=True)
@utils.retry_on_failure('Retrying create disk snapshot')
@utils.throw_cloudify_exceptions
def create(disk_name, **kwargs):
    snapshot_type = kwargs.get('snapshot_type')
    snapshot_name = _get_backupname(kwargs)
    if not kwargs.get("snapshot_incremental"):
        ctx.logger.info("Create backup for VM is unsupported.")
        return

    gcp_config = utils.get_gcp_config()
    ctx.logger.info("Disk name: {0}".format(disk_name))
    if disk_name:
        snapshot = Snapshot(gcp_config,
                            ctx.logger,
                            name=snapshot_name,
                            description=snapshot_type)
        snapshot.create(disk_name=disk_name)


@operation(resumable=True)
@utils.retry_on_failure('Retrying deleting snapshot')
@utils.throw_cloudify_exceptions
def delete(**kwargs):
    snapshot_name = _get_backupname(kwargs)
    if not kwargs.get("snapshot_incremental"):
        ctx.logger.info("Delete backup for VM is unsupported.")
        return

    gcp_config = utils.get_gcp_config()
    snapshot = Snapshot(gcp_config,
                        ctx.logger,
                        name=snapshot_name)
    snapshot.delete()
