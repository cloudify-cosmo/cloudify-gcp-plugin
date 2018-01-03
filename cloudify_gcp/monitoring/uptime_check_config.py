# #######
# Copyright (c) 2017 GigaSpaces Technologies Ltd. All rights reserved
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

# Standard library imports
from __future__ import unicode_literals

# Third-party imports
from cloudify import ctx
from cloudify.decorators import operation
from cloudify.exceptions import NonRecoverableError

# Local imports
from .. import utils
from ..gcp import check_response
from ..monitoring import MonitoringBase


UPTIME_CHECKCONFIG_MAP = {
    'name': 'name',
    'display_name': 'displayName',
    'period': 'period',
    'timeout': 'timeout',
    'content_matchers': 'contentMatchers',
    'content': 'content',
    'selected_regions': 'selectedRegions',
    'is_internal': 'isInternal',
    'internal_checkers': 'internalCheckers',
    'resource': 'resource',
    'monitored_resource': 'monitoredResource',
    'resource_group': 'resourceGroup',
    'check_request_type': 'check_request_type',
    'http_check': 'httpCheck',
    'tcp_check': 'httpCheck',
    'type': 'type',
    'labels': 'labels',
    'group_id': 'groupId',
    'resource_type': 'resourceType',
    'use_ssl': 'useSsl',
    'path': 'path',
    'port': 'port',
    'auth_info': 'authInfo',
    'username': 'username',
    'password': 'password',
    'mask_headers': 'maskHeaders',
    'headers': 'headers',
}

INTERNAL_CHECKER_CONFIG = {
    'project_id': 'projectId',
    'network': 'network',
    'gcp_zone': 'gcpZone',
    'checker_id': 'checkerId',
    'display_name': 'displayName',
}


class UptimeCheckConfig(MonitoringBase):
    def __init__(self,
                 config,
                 logger,
                 name,
                 display_name,
                 period,
                 timeout,
                 resource,
                 check_request_type,
                 content_matchers=None,
                 selected_regions=None,
                 is_internal=False,
                 internal_checkers=None):
        """
        Create Uptime Check Config Group object

        :param config: dictionary with project properties: path to auth file,
        project and zone
        :param logger: logger object that the class methods will be logging to
        """
        super(UptimeCheckConfig, self).__init__(config, logger, name)
        self.name = name
        self.display_name = display_name
        self.period = period
        self.timeout = timeout
        self.resource = resource
        self.check_request_type = check_request_type
        self.content_matchers = content_matchers
        self.selected_regions = selected_regions
        self.is_internal = is_internal
        self.internal_checkers = internal_checkers

    @check_response
    def create(self):
        return self.discovery_monitoring.uptimeCheckConfigs().create(
            body=self.to_dict(),
            parent=self.project_path).execute()

    @check_response
    def update(self):
        return self.discovery_monitoring.uptimeCheckConfigs(
        ).patch(**{'body': self.to_dict(),
                   'uptimeCheckConfig.name': self.name}).execute()

    @check_response
    def delete(self):
        return self.discovery_monitoring.uptimeCheckConfigs().delete(
            name=self.name).execute()

    @check_response
    def get(self):
        return self.discovery_monitoring.uptimeCheckConfigs().get(
            name=self.name).execute()

    @property
    def project_path(self):
        return 'projects/trammell-project'
        # return 'projects/{0}'.format(self.project)

    def to_dict(self):
        uptime_check_conf_req = dict()
        gcp_display_name_key = UPTIME_CHECKCONFIG_MAP['display_name']
        gcp_period_key = UPTIME_CHECKCONFIG_MAP['period']
        gcp_timeout_key = UPTIME_CHECKCONFIG_MAP['timeout']
        gcp_internal_check_key = UPTIME_CHECKCONFIG_MAP['internal_checkers']
        gcp_content_matchers_key = UPTIME_CHECKCONFIG_MAP['content_matchers']
        gcp_content_key = UPTIME_CHECKCONFIG_MAP['content']
        gcp_selected_regions_key = UPTIME_CHECKCONFIG_MAP['selected_regions']

        if all([self.display_name, self.period, self.timeout]):
            uptime_check_conf_req['displayName'] = gcp_display_name_key
            uptime_check_conf_req['period'] = gcp_period_key
            uptime_check_conf_req['timeout'] = gcp_timeout_key

            if self.is_internal:
                gcp_is_internal_key = UPTIME_CHECKCONFIG_MAP['is_internal']
                uptime_check_conf_req[gcp_is_internal_key] = self.is_internal

                ## Populate ``internal_checkers`` config
                internal_checkers_list = []
                for internal_checker in self.internal_checkers:
                    gcp_internal_check_conf = dict()
                    for key, value in INTERNAL_CHECKER_CONFIG.iteritems():
                        if internal_checker.get(key):
                            gcp_internal_check_conf[value] = \
                                internal_checker[key]

                    internal_checkers_list.append(gcp_internal_check_conf)

                if internal_checkers_list:
                    uptime_check_conf_req[gcp_internal_check_key]\
                        = internal_checkers_list

            content_matchers_list = []
            for content_matcher in self.content_matchers:
                content_config = dict()
                if content_matcher.get('content'):
                    content_config[gcp_content_key]\
                        = content_matcher['content']
                    content_matchers_list.append(content_config)

            if content_matchers_list:
                uptime_check_conf_req[gcp_content_matchers_key]\
                    = content_matchers_list

            if self.selected_regions:
                uptime_check_conf_req[gcp_selected_regions_key]\
                    = self.selected_regions

        else:
            raise NonRecoverableError(
                'Uptime check config must contains all required fields')

        return uptime_check_conf_req


@operation
@utils.throw_cloudify_exceptions
def create(name, display_name, period, timeout,
           content_matchers, selected_regions,
           is_internal=False, internal_checkers=None, **kwargs):

    name = utils.get_final_resource_name(name)
    gcp_config = utils.get_gcp_config()
    upcheck_config = UptimeCheckConfig(gcp_config,
                                       ctx.logger,
                                       name=name,
                                       display_name=display_name,
                                       period=period,
                                       timeout=timeout,
                                       resource=None,
                                       check_request_type=None,
                                       content_matchers=content_matchers,
                                       selected_regions=selected_regions,
                                       is_internal=is_internal,
                                       internal_checkers=internal_checkers,)

    response = utils.create(upcheck_config)

    # Update the name of the group set by api
    upcheck_config.name = response.get('name')
    ctx.logger.info('Monitoring group {0} created successfully {1}'
                    .format(upcheck_config.name, response))


@operation
@utils.throw_cloudify_exceptions
def delete(**kwargs):
    pass


@operation
@utils.throw_cloudify_exceptions
def update(name, display_name, period, timeout, resource,
           check_request_type, content_matchers, selected_regions,
           is_internal, internal_checkers,  **kwargs):

    name = utils.get_final_resource_name(name)
    gcp_config = utils.get_gcp_config()
    upcheck_config = UptimeCheckConfig(gcp_config,
                                       ctx.logger,
                                       name=name,
                                       display_name=display_name,
                                       period=period,
                                       timeout=timeout,
                                       resource=resource,
                                       check_request_type=check_request_type,
                                       content_matchers=content_matchers,
                                       selected_regions=selected_regions,
                                       is_internal=is_internal,
                                       internal_checkers=internal_checkers,)

    response = utils.create(upcheck_config)

    # Update the name of the group set by api
    upcheck_config.name = response.get('name')
    ctx.logger.info('Monitoring group {0} created successfully {1}'
                    .format(upcheck_config.name, response))
