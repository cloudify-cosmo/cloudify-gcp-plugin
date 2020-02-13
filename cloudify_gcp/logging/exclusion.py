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
from cloudify.exceptions import NonRecoverableError
from cloudify_gcp.gcp import check_response

from .. import utils
from .. import constants
from ..logging import BillingAccountBase


class LoggingExclusion(BillingAccountBase):
    def __init__(self, config, logger, exclusion_type, parent=None,
                 log_exclusion=None, name=None, update_mask=None):
        super(LoggingExclusion, self).__init__(
            config, logger, name or parent)
        self.parent = parent
        self.log_exclusion = log_exclusion
        self.name = name
        self.update_mask = update_mask

        if exclusion_type == 'BillingAccount':
            self.exclusion_discovery = \
                self.discovery.billingAccounts().exclusions()
        elif exclusion_type == 'Folder':
            self.exclusion_discovery = \
                self.discovery.folders().exclusions()
        elif exclusion_type == 'Organization':
            self.exclusion_discovery = \
                self.discovery.organizations().exclusions()
        elif exclusion_type == 'Project':
            self.exclusion_discovery = \
                self.discovery.projects().exclusions()
        else:
            raise NonRecoverableError('Invalid sink type of {}'.format(
                exclusion_type))

    @check_response
    def create(self):
        return self.exclusion_discovery.create(
            parent=self.parent,
            body=self.log_exclusion).execute()

    @check_response
    def delete(self):
        return self.exclusion_discovery.delete(
            name=self.name).execute()

    @check_response
    def update(self):
        return self.exclusion_discovery.patch(
            body=self.log_exclusion, name=self.name,
            updateMask=self.update_mask).execute()


@operation(resumable=True)
@utils.throw_cloudify_exceptions
def create(ctx, parent, log_exclusion, exclusion_type, **kwargs):
    if utils.resorce_created(ctx, constants.NAME):
        return

    gcp_config = utils.get_gcp_config()
    billing_account_exclusion = LoggingExclusion(
        gcp_config, ctx.logger, exclusion_type, parent, log_exclusion,
        **kwargs)
    resource = utils.create(billing_account_exclusion)
    ctx.instance.runtime_properties[
        constants.NAME] = '{}/exclusions/{}'.format(
            parent, resource[constants.NAME])


@operation(resumable=True)
@utils.retry_on_failure('Retrying deleting logging exclusion')
@utils.throw_cloudify_exceptions
def delete(exclusion_type, **kwargs):
    gcp_config = utils.get_gcp_config()
    props = ctx.instance.runtime_properties

    if props.get(constants.NAME):
        billing_account_exclusion = LoggingExclusion(
            gcp_config, ctx.logger, exclusion_type,
            name=props[constants.NAME])

        utils.delete_if_not_external(billing_account_exclusion)


@operation(resumable=True)
@utils.throw_cloudify_exceptions
def update(parent, log_exclusion, exclusion_type, **kwargs):
    gcp_config = utils.get_gcp_config()
    current_resource_name = ctx.instance.runtime_properties[constants.NAME]
    billing_account_exclusion = LoggingExclusion(
        gcp_config, ctx.logger, exclusion_type, parent, log_exclusion,
        name=current_resource_name, **kwargs)
    billing_account_exclusion.update()
