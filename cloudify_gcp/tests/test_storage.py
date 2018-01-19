########
# Copyright (c) 2018 GigaSpaces Technologies Ltd. All rights reserved
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
from cloudify_gcp import storage
from . import TestGCP


class TestStorageWithCTX(TestGCP):

    def test_object_init(self):
        config = {
            "auth": "auth",
            "project": "project",
            "zone": "zone",
        }
        object_check = storage.Object(config, self.ctxmock.logger, "abc",
                                      "bucket")
        self.assertEqual(object_check.config, config)
        self.assertEqual(object_check.bucket, "bucket")

        object_check = storage.Object(config, self.ctxmock.logger, "abc")
        self.assertEqual(object_check.config, config)
        self.assertEqual(object_check.bucket, "project")

    def test_bucket_init(self):
        config = {
            "auth": "auth",
            "project": "project",
            "zone": "zone",
        }
        bucket_check = storage.Bucket(config, self.ctxmock.logger, "abc")
        self.assertEqual(bucket_check.config, config)
        self.assertEqual(bucket_check.name, "abc")

        bucket_check = storage.Bucket(config, self.ctxmock.logger)
        self.assertEqual(bucket_check.config, config)
        self.assertEqual(bucket_check.name, "project")
