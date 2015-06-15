########
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

import json

import Crypto
import httplib2
from googleapiclient.discovery import build
from oauth2client.client import SignedJwtAssertionCredentials


class GoogleCloudPlatform(object):
    """
    Class using google-python-api-client library to connect to Google Cloud
    Platform.
    """
    COMPUTE_SCOPE = 'https://www.googleapis.com/auth/compute'

    def __init__(self, config, logger):
        """
        GoogleCloudPlatform class constructor.
        Create compute object that will be making
        Google Cloud Platform Compute API calls.

        :param auth: path to service account JSON file
        :param project: dictionary with project properties
        :param scope: scope string of GCP connection
        :param logger: logger object that the class methods will be logging to
        :return:
        """
        self.auth = config['auth']
        self.project = config['project']
        self.zone = config['zone']
        self.scope = self.COMPUTE_SCOPE
        self.logger = logger.getChild('GCP')
        self.compute = self.create_compute()

    def create_compute(self):
        """
        Create Google Cloud Compute object and perform authentication.

        :return: compute object
        :raise: GCPError if there is a problem with service account JSON file:
        e.g. the file is not under the given path or it has wrong permissions
        """
        Crypto.Random.atfork()
        try:
            with open(self.auth) as f:
                account_data = json.load(f)
            credentials = SignedJwtAssertionCredentials(
                account_data['client_email'],
                account_data['private_key'],
                scope=self.scope)
            http = httplib2.Http()
            credentials.authorize(http)
            return build('compute', 'v1', http=http)
        except IOError as e:
            self.logger.error(str(e))
            raise GCPError(str(e))

    def get_common_instance_metadata(self):
        """
        Get project's common instance metadata.

        :return: CommonInstanceMetadata list extracted from REST response get
        project metadata.
        """
        self.logger.info(
            'Get commonInstanceMetadata for project {0}'.format(self.project))
        metadata = self.compute.projects().get(project=self.project).execute()
        return metadata['commonInstanceMetadata']


class GCPError(Exception):
    """
    Exception raised from GoogleCloudPlatform class.
    """
    def __init__(self, message):
        super(GCPError, self).__init__(message)
