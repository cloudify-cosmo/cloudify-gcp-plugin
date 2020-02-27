########
# Copyright (c) 2015-2020 Cloudify Platform Ltd. All rights reserved
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

from cosmo_tester.framework.testenv import TestCase

from . import GCPTest


class GCPDiskTest(GCPTest, TestCase):
    blueprint_name = 'disk/attach-disk.yaml'

    inputs = (
            'project',
            'network',
            'zone',
            'gcp_auth',
            'image_id',
            )

    def assertions(self):
        self.assertEqual(
            self.get_instance('vm')[
                'runtime_properties']['disks'][0]['source'],
            self.get_instance('boot_disk')['runtime_properties']['selfLink'])
