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
from plugin.gcp.service import GoogleCloudPlatform


class Disk(GoogleCloudPlatform):
    def __init__(self,
                 config,
                 logger,
                 name,
                 image=None,
                 size_gb=None):
        super(Disk, self).__init__(config, logger)
        self.image = image
        self.name = name
        self.sizeGb = size_gb

    def to_dict(self):
        body = {
            'description': 'Cloudify generated disk',
            'name': self.name
        }
        if self.image:
            body['sourceImage'] = self.image
        if self.sizeGb:
            body['sizeGb'] = self.sizeGb
        return body

    def disk_to_insert_instance_dict(self, mount_name):
        disk_info = self.get()
        body = {
            'deviceName': mount_name,
            'boot': False,
            'mode': 'READ_WRITE',
            'autoDelete': False,
            'source': disk_info['selfLink']
        }
        return body

    def get(self):
        return self.compute.disks().get(
            project=self.project,
            zone=self.zone,
            disk=self.name).execute()

    def create(self):
        return self.compute.disks().insert(
            project=self.project,
            zone=self.zone,
            body=self.to_dict()).execute()

    def delete(self):
        return self.compute.disks().delete(
            project=self.project,
            zone=self.zone,
            disk=self.name).execute()
