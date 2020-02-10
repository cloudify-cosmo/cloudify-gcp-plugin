# #######
# Copyright (c) 2018-2020 Cloudify Platform Ltd. All rights reserved
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
from cloudify import ctx
from cloudify.decorators import operation
from cloudify_gcp.gcp import check_response

from .. import utils
from ..logging import BillingAccountBase


class ProjectMetrics(BillingAccountBase):
    def get_discovery(self):
        return self.discovery.projects().metrics()

    def __init__(self, config, logger, parent=None,
                 log_metric=None, name=None):
        super(ProjectMetrics, self).__init__(
            config, logger, name or parent)
        self.parent = parent
        self.log_metric = log_metric
        self.name = name

    @check_response
    def create(self):
        return self.get_discovery().create(
            parent=self.parent,
            body=self.log_metric).execute()

    @check_response
    def delete(self):
        return self.get_discovery().delete(
            metricName=self.name).execute()

    @check_response
    def update(self):
        return self.get_discovery().update(
            body=self.log_metric, metricName=self.name).execute()


@operation
@utils.throw_cloudify_exceptions
def create(ctx, parent, log_metric, **kwargs):
    gcp_config = utils.get_gcp_config()
    folder_sink = ProjectMetrics(
        gcp_config, ctx.logger, parent, log_metric, **kwargs)
    resource = utils.create(folder_sink)
    ctx.instance.runtime_properties['name'] = "{}/metrics/{}".format(
        parent, resource['name'])


@operation
@utils.retry_on_failure('Retrying deleting folder sink')
@utils.throw_cloudify_exceptions
def delete(**kwargs):
    gcp_config = utils.get_gcp_config()
    folder_sink = ProjectMetrics(
        gcp_config, ctx.logger, name=ctx.instance.runtime_properties['name'])

    utils.delete_if_not_external(folder_sink)


@operation
@utils.throw_cloudify_exceptions
def update(parent, log_metric, **kwargs):
    gcp_config = utils.get_gcp_config()
    current_resource_name = ctx.instance.runtime_properties['name']
    folder_sink = ProjectMetrics(
        gcp_config, ctx.logger, parent, log_metric,
        name=current_resource_name, **kwargs)
    folder_sink.update()
