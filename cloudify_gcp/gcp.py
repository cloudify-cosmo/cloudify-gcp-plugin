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
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from functools import wraps
from os.path import basename

import httplib2
from Crypto.Random import atfork
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from oauth2client.service_account import ServiceAccountCredentials

from . import constants


def check_response(func):
    """
    Decorator checking first REST response.
    :return:
    """
    def _decorator(self, *args, **kwargs):
        response = func(self, *args, **kwargs)
        if 'error' in response:
            self.logger.error('Response with error {0}'
                              .format(response['error']))

            raise GCPError(response['error'])
        return response
    return wraps(func)(_decorator)


class GoogleCloudPlatform(object):
    """
    Class using google-python-api-client library to connect to Google Cloud
    Platform.
    """

    def __init__(self, config, logger, name,
                 additional_settings=None,
                 scope=constants.COMPUTE_SCOPE,
                 discovery=constants.COMPUTE_DISCOVERY,
                 api_version=constants.API_V1):
        """
        GoogleCloudPlatform class constructor.
        Create API discovery object that will be making GCP REST API calls.

        :param config: dictionary with project properties: path to auth file,
        project and zone
        :param logger: logger object that the class methods will be logging to
        :param name: name of GCP resource represented by this object
        :param scope: scope string of GCP connection
        :param discovery: name of Google service
        :param api_version: version of used API to communicate with GCP
        :return:
        """
        self.auth = config['auth']
        self.project = config['project']
        self.zone = config['zone']
        self.config = config
        self.scope = scope
        self.name = name
        self.logger = logger.getChild('GCP')
        self.__discovery = discovery
        self.api_version = api_version
        self.body = additional_settings if additional_settings else {}

    @property
    def discovery(self):
        """
        Lazily load the discovery so we don't make API calls during __init__
        """
        if hasattr(self, '_discovery'):
            return self._discovery
        self._discovery = self.create_discovery(
                self.__discovery, self.scope, self.api_version)
        return self._discovery

    def create_discovery(self, discovery, scope, api_version):
        """
        Create Google Cloud API discovery object and perform authentication.

        :param discovery: name of the API discovery to be created
        :param scope: scope the API discovery will have
        :param api_version: version of the API
        :return: discovery object
        :raise: GCPError if there is a problem with service account JSON file:
        e.g. the file is not under the given path or it has wrong permissions
        """
        # Crypto.Random.atfork() must be called here because celery doesn't do
        # it
        atfork()
        if hasattr(self.auth, 'get'):
            creds_func = ServiceAccountCredentials.from_json_keyfile_dict
        else:
            creds_func = ServiceAccountCredentials.from_json_keyfile_name

        try:
            credentials = creds_func(
                    self.auth,
                    scopes=scope)
            http = httplib2.Http()
            credentials.authorize(http)
            return build(discovery, api_version, http=http)
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
        metadata = self.discovery.projects().get(
            project=self.project).execute()
        return metadata['commonInstanceMetadata']

    @property
    def ZONES(self):
        if not hasattr(self, '_ZONES'):
            zones = {}
            request = self.discovery.zones().list(project=self.project)
            while request is not None:
                response = request.execute()

                for zone in response['items']:
                    zones[zone['name']] = zone
                    zone['region_name'] = basename(zone['region'])

                request = self.discovery.zones().list_next(
                        previous_request=request,
                        previous_response=response)

        self._ZONES = zones
        return self._ZONES


class GCPError(Exception):
    """
    Exception raised from GoogleCloudPlatform class.
    """
    def __init__(self, message):
        super(GCPError, self).__init__(message)


def is_missing_resource_error(error):
    return isinstance(error, HttpError) and error.resp.status == 404


def is_resource_used_error(error):
    return isinstance(error, HttpError) and error.resp.status == 400
