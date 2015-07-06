# #######
# Copyright (c) 2014 GigaSpaces Technologies Ltd. All rights reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
#    * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    * See the License for the specific language governing permissions and
#    * limitations under the License.
from googleapiclient.http import MediaFileUpload
from googleapiclient.http import HttpError

from gcp.gcp import GoogleCloudPlatform
from gcp.gcp import GCPError
from gcp.compute import constants


class Storage(GoogleCloudPlatform):
    def __init__(self,
                 config,
                 logger,
                 name,
                 bucket=None):
        """
        Create GCP Storage object

        :param config:
        :param logger: logger
        :param name: name of the Object to save in the Cloud Storage
        :param bucket: name of the bucket to store Object in,
        if other than project name
        """
        super(Storage, self).__init__(config,
                                      logger,
                                      name,
                                      scope=constants.STORAGE_SCOPE_RW,
                                      discovery=constants.STORAGE_DISCOVERY)
        self.config = config
        self.bucket = bucket if bucket else self.project

    def upload_to_bucket(self, path):
        media = MediaFileUpload(path,
                                chunksize=constants.CHUNKSIZE,
                                resumable=True)
        request = self.discovery.objects().insert(bucket=self.bucket,
                                                  name=self.name,
                                                  media_body=media)
        response = None
        while response is None:
            try:
                _, response = request.next_chunk()
            except HttpError as e:
                raise GCPError(e.message)
        return response['selfLink']
