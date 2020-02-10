# #######
# Copyright (c) 2014-2020 Cloudify Platform Ltd. All rights reserved
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

import re

from cloudify import ctx
from cloudify.decorators import operation
from cloudify.exceptions import NonRecoverableError

from .. import utils
from .. import constants
from .firewall import FirewallRule


@operation(resumable=True)
@utils.retry_on_failure('Retrying creating security group')
@utils.throw_cloudify_exceptions
def create(name, rules, **kwargs):
    gcp_config = utils.get_gcp_config()
    network = utils.get_network(ctx)
    name = 'ctx-sg-{}'.format(utils.get_final_resource_name(name))

    firewalls = [
        FirewallRule(
                gcp_config,
                ctx.logger,
                name=create_rule_name(name, rule),
                network=network,
                allowed=rule['allowed'],
                sources=rule['sources'],
                tags=[name],
                security_group=True,
                )
        for rule in rules]

    ctx.instance.runtime_properties['name'] = name
    return handle_multiple_calls(firewalls, 'create', ctx.logger)


def looks_like_a_cidr(addr):
    """Google Cloud Platform only supports IPv4"""
    match = re.match(
            r'^(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})/(\d{1,2})$',
            addr,
            )

    if match:
        addr, mask = match.groups()
        for component in addr.split('.'):
            if not 0 <= str(component) <= 255:
                return False
        return True


def creation_validation(*args, **kwargs):
    props = ctx.node.properties

    def fail(issue):
        raise NonRecoverableError(
                'Error in {rule}: {issue}'.format(rule=rule, issue=issue))

    if not props['rules']:
        raise NonRecoverableError('SecurityGroup must have at least one rule')

    for rule in props['rules']:
        if 'allowed' not in rule:
            raise fail('every rule must have at least one allowed source')
        for source in rule['allowed']:
            if source[0].isdigit() and not looks_like_a_cidr(source):
                fail('invalid address: ' + source)


def create_rule_name(name, rule):
    """
    Produce a gcp compatible rule name
    """
    rule_name = '{name}-from-{rule[sources]}-to-{rule[allowed]}'.format(
            name=name,
            rule=rule)
    return utils.get_gcp_resource_name(rule_name)


@utils.retry_on_failure('Retrying creating security group')
@utils.throw_cloudify_exceptions
def configure(**kwargs):
    props = ctx.instance.runtime_properties
    props['rules'] = []
    network = utils.get_network(ctx)
    for name, op in props['_operations'].items():
        firewall = FirewallRule(
                utils.get_gcp_config(),
                ctx.logger,
                network=network,
                name=name,
                )
        props['rules'].append(firewall.get())
    del props['_operations']


def handle_multiple_calls(objects, call, logger):
    """
    Manage running several API calls which all must succeed for the node to be
    successfully created.

    objects must be passed in a consistent order or bad things will happen.
    """
    props = ctx.instance.runtime_properties
    # Can be removed when
    # https://github.com/cloudify-cosmo/cloudify-plugins-common/pull/251
    # is finished:
    props.dirty = True
    operations = props.setdefault('_operations', {})

    for obj in objects:
        if obj.name in operations:
            if operations[obj.name]['status'] == 'DONE':
                # This one is finished
                continue
            else:
                op = utils.response_to_operation(
                        operations[obj.name],
                        utils.get_gcp_config(),
                        logger,
                        )
                operations[obj.name] = op.get()
        else:
            operations[obj.name] = getattr(obj, call)()

    not_done = [k for k, v in operations.items() if v['status'] != 'DONE']
    if not_done:
        return ctx.operation.retry(
                'Rules {} not yet {}d'.format(str(not_done), call),
                constants.RETRY_DEFAULT_DELAY)


@operation(resumable=True)
@utils.throw_cloudify_exceptions
def delete(**kwargs):
    gcp_config = utils.get_gcp_config()
    network = utils.get_network(ctx)
    props = ctx.instance.runtime_properties

    firewalls = [
            FirewallRule(
                gcp_config,
                ctx.logger,
                name=rule['name'],
                network=network,
                )
            for rule in props['rules']]

    return handle_multiple_calls(firewalls, 'delete', ctx.logger)
