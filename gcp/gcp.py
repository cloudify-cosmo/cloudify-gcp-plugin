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

from gcp.compute import utils


class GoogleCloudPlatform(object):
    """
    Class using google-python-api-client library to connect to Google Cloud
    Platform.
    """

    def __init__(self, config, logger, name, scope=utils.COMPUTE_SCOPE,
                 discovery=utils.COMPUTE_DISCOVERY):
        """
        GoogleCloudPlatform class constructor.
        Create API discovery object that will be making GCP REST API calls.

        :param config: dictionary with project properties: path to auth file,
        project and zone
        :param scope: scope string of GCP connection
        :param logger: logger object that the class methods will be logging to
        :return:
        """
        self.auth = config['auth']
        self.project = config['project']
        self.zone = config['zone']
        self.scope = scope
        self.name = name
        self.logger = logger.getChild('GCP')
        self.discovery = self.create_discovery(discovery, self.scope)

    def create_discovery(self, discovery, scope):
        """
        Create Google Cloud API discovery object and perform authentication.

        :param discovery: name of the API discovery to be created
        :param scope: scope the API discovery will have
        :return: discovery object
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
                scope=scope)
            http = httplib2.Http()
            credentials.authorize(http)
            return build(discovery, 'v1', http=http)
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
        metadata = self.discovery.projects().get(project=self.project).execute()
        return metadata['commonInstanceMetadata']


class GCPError(Exception):
    """
    Exception raised from GoogleCloudPlatform class.
    """
    def __init__(self, message):
        super(GCPError, self).__init__(message)
