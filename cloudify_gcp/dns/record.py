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

from time import sleep

from cloudify import ctx
from cloudify.decorators import operation
from cloudify.exceptions import NonRecoverableError

from .. import utils
from .. import constants
from .dns import DNSZone


def get_current_records(zone, name=None, type=None):
    """Expects a DNSZone object and the DNS name and record type to filter
    on"""
    return zone.list_records(name=name, type=type)


def generate_changes(dns_zone, action, data):
    """
    Produces a change request (additions, deletions) with the specified data
    """
    return dns_zone.discovery.changes().create(
            project=utils.get_gcp_config()['project'],
            managedZone=dns_zone.name,
            body={action: data})


def wait_for_change_completion(dns_zone, response):
    while response['status'] == 'pending':
        sleep(3)
        response = dns_zone.discovery.changes().get(
                project=utils.get_gcp_config()['project'],
                managedZone=dns_zone.name,
                changeId=response['id'],
                ).execute()
    return response


def creation_validation(*args, **kwargs):
    rels = ctx.instance.relationships

    rel_types = [rel.type for rel in rels]

    if (
            'cloudify.relationships.gcp.'
            'dns_record_contained_in_zone') not in rel_types:
        raise NonRecoverableError('record must be contained in a zone')

    for rel in utils.get_relationships(
            rels,
            filter_relationships=[
                'cloudify.relationships.gcp.dns_record_connected_to_instance']
            ):
        instance_rels = utils.get_relationships(
            rel.target.instance.relationships,
            filter_relationships=[
                'cloudify.relationships.gcp.instance_connected_to_ip',
                ],
            )
        if len(instance_rels) < 1:
            raise NonRecoverableError(
                'target instance must have an external or staticIP address.')


def traverse_item_heirarchy(root, keys):
    """
    Given a root and a list of keys, follow each key to get the value.

    e.g.
        traverse_item_heirarchy(root, [0, 'a', 'b'])
    is equivalent to
        root[0]['a']['b']
    """
    item = root
    for key in keys:
        item = item[key]
    return item


@operation(resumable=True)
@utils.throw_cloudify_exceptions
def create(type, name, resources, ttl, **kwargs):
    if utils.resource_created(ctx, 'created'):
        return

    ctx.instance.runtime_properties['created'] = False

    gcp_config = utils.get_gcp_config()

    zone = utils.get_relationships(
            ctx,
            filter_relationships='cloudify.relationships.gcp.'
                                 'dns_record_contained_in_zone',
            )[0].target.instance

    dns_zone = DNSZone(
            gcp_config,
            ctx.logger,
            zone.runtime_properties[constants.NAME],
            dns_name=zone.runtime_properties['dnsName'],
            )

    if not name:
        name = ctx.node.id
    ctx.instance.runtime_properties[constants.NAME] = name

    mappings = {
        'dns_record_connected_to_instance':
            ['networkInterfaces', 0, 'accessConfigs', 0, 'natIP'],
        'dns_record_connected_to_ip':
            ['address'],
        }

    rels = utils.get_relationships(
            ctx,
            filter_relationships=[
                'cloudify.relationships.gcp.dns_record_connected_to_instance',
                'cloudify.relationships.gcp.dns_record_connected_to_ip'
                ],
            )
    for rel in rels:
        item_path = mappings[rel.type.split('.')[-1]]
        item = traverse_item_heirarchy(
            rel.target.instance.runtime_properties,
            item_path)
        resources.append(item)

    response = generate_changes(dns_zone, 'additions', [{
            "name": '{}.{}'
                    .format(name, zone.runtime_properties['dnsName']),
            "ttl": ttl,
            "type": type,
            "rrdatas": resources}]).execute()

    response = wait_for_change_completion(dns_zone, response)

    if response['status'] != 'done':
        raise NonRecoverableError('unexpected response status: {}'.format(
            response))

    ctx.instance.runtime_properties['created'] = True


@operation(resumable=True)
@utils.retry_on_failure('Retrying deleting DNS Record')
@utils.throw_cloudify_exceptions
def delete(**_):
    gcp_config = utils.get_gcp_config()
    if ctx.instance.runtime_properties.get('created'):

        zone = utils.get_relationships(
                ctx,
                filter_relationships='cloudify.relationships.gcp.'
                                     'dns_record_contained_in_zone',
                )[0].target.instance
        dns_zone = DNSZone(
                gcp_config,
                ctx.logger,
                zone.runtime_properties[constants.NAME],
                dns_name=zone.runtime_properties['dnsName'],
                )

        rrsets = get_current_records(
                dns_zone,
                name=ctx.instance.runtime_properties[constants.NAME],
                type=ctx.node.properties['type'],
                )

        wait_for_change_completion(
                dns_zone,
                generate_changes(dns_zone, 'deletions', rrsets).execute())

        ctx.instance.runtime_properties.pop('created', None)


def validate_contained_in(**_):
    if ctx.target.type != 'cloudify.nodes.gcp.DNSZone' or \
            ctx.source.type != 'cloudify.nodes.gcp.DNSRecord' or \
            ctx.target.type != 'cloudify.gcp.nodes.DNSZone' or \
            ctx.source.type != 'cloudify.gcp.nodes.DNSRecord':
        raise NonRecoverableError(
                'Unsupported types for {} relationship'.format(ctx.type))
