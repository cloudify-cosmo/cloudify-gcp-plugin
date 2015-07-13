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

from gcp import check_response
from gcp import GoogleCloudPlatform
from gcp import GCPError
from compute import constants


class Object(GoogleCloudPlatform):
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
        super(Object, self).__init__(config,
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

    def delete(self):
        return self.discovery.objects().delete(bucket=self.bucket,
                                               name=self.name).execute()


class Bucket(GoogleCloudPlatform):
    def __init__(self,
                 config,
                 logger,
                 name=None):
        """
        Create Bucket object

        :param config:
        :param logger:
        :param name: name of the bucket, if None project name will be taken
        """
        super(Bucket, self).__init__(config,
                                     logger,
                                     name,
                                     scope=constants.STORAGE_SCOPE_RW,
                                     discovery=constants.STORAGE_DISCOVERY)
        self.name = self.name if name else self.project

    @check_response
    def create(self):
        body = {'name': self.name}
        return self.discovery.buckets().create(project=self.project,
                                               body=body).execute()

    @check_response
    def delete(self):
        return self.discovery.buckets().delete(bucket=self.name).execute()

    @check_response
    def list(self):
        response = self.discovery.buckets().list(
            project=self.project).execute()
        return response['items']
