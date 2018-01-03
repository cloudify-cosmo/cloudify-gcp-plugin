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


TYPED_VALUE_TIME_SERIES_MAP = {
    'bool_value': 'boolValue',
    'int64_value': 'int64Value',
    'double_value': 'doubleValue',
    'string_value': 'stringValue',
    'distribution_value': 'distributionValue',

}


class TimeSeries(MonitoringBase):
    def __init__(self,
                 config,
                 logger,
                 time_series,
                 name,):
        """
        Create Monitoring TimeSeries object
        :param config: dictionary with project properties: path to auth file,
        project and zone
        :param logger: logger object that the class methods will be logging to
        :param time_series: The new data to be added to a list of time series
        More info can be found on google api doc
        https://cloud.google.com/monitoring/api/ref_v3/rest/v3/TimeSeries
        """
        super(TimeSeries, self).__init__(config, logger, name)
        self.time_series = time_series

    @check_response
    def create(self):
        return self.discovery_monitoring.timeSeries().create(
            body=self.to_dict(),
            name=self.project_path).execute()

    @check_response
    def delete(self):
        pass

    @property
    def project_path(self):
        return 'projects/{0}'.format(self.project)

    def to_dict(self):
        time_series = dict()
        time_series_list = []
        for item in self.time_series:
            gcp_object = dict()
            # metric, resource, points are required field and should be there
            if all([k in item for k in ('metric', 'resource', 'points')]):
                gcp_object['metric'] = item['metric']
                gcp_object['resource'] = item['resource']

                # metric_kind is an optional value
                if item.get('metric_kind'):
                    gcp_object['metricKind'] = item['metric_kind']

                # value_type is an optional value
                if item.get('valueType'):
                    gcp_object['valueType'] = item['value_type']

                point_list = []
                for point in item['points']:
                    gcp_point = dict()
                    if all([k in point for k in ('interval', 'value')]):

                        # Handle interval object
                        gcp_interval = dict()
                        gcp_typed_value = dict()

                        time_interval = point['interval']
                        typed_value = point['value']
                        if all([k in time_interval
                                for k in ('start_time', 'end_time')]):

                            gcp_interval['endTime'] = time_interval['end_time']
                            gcp_interval['startTime'] = time_interval['start_time']

                            # Handle value object
                            for k, v in typed_value.iteritems():
                                if k == 'distribution_value':
                                    # TODO later on
                                    pass
                                else:
                                    gcp_typed_value[
                                        TYPED_VALUE_TIME_SERIES_MAP[k]] = v
                    else:
                        raise NonRecoverableError(
                            'Points {} should contains both interval and '
                            'value'.format(point))

                    gcp_point['interval'] = gcp_interval
                    gcp_point['value'] = gcp_typed_value
                    point_list.append(gcp_point)

                gcp_object['points'] = point_list
                time_series_list.append(gcp_object)

            else:
                raise NonRecoverableError(
                    'Item {} should contains both metric and resource'
                    ''.format(item))

        time_series['timeSeries'] = time_series_list
        return time_series


@operation
@utils.throw_cloudify_exceptions
def create(time_series, **kwargs):
    if isinstance(time_series, list):
        ctx.logger.info(
            'This is the list of time series {}'.format(time_series))

    name = utils.get_gcp_resource_name(ctx.instance.id)
    gcp_config = utils.get_gcp_config()
    if time_series:
        time_series_object = TimeSeries(gcp_config, ctx.logger,
                                        time_series, name=name)

        response = time_series_object.create()
        ctx.logger.info('Response is {}'.format(response))

    else:
        raise NonRecoverableError(
            'time_series cannot be empty list !!')
