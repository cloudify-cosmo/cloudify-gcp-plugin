from cloudify import ctx as _ctx
from cloudify.context import NodeContext
from cloudify.decorators import operation
from cloudify.exceptions import NonRecoverableError
from cloudify_common_sdk.utils import desecretize_client_config

from .. import utils
from ..container_engine.cluster import Cluster

TYPES_MATRIX = {
    'projects.zones.clusters': (
        Cluster, 'gke', 'name'
    )
}


@operation
def initialize(resource_config=None, zones=None, ctx=None, **_):
    """ Initialize an cloudify.nodes.gcp.GCP node.
    This checks for resource_types in resource config and
        zones in zones.
    :param resource_config: A dict with key resource_types,
      a list of gcp types like projects.zones.clusters.
    :param zones: A list of zones, like [europe-west1-b].
    :param ctx: Cloudify CTX
    :param _:
    :return:
    """

    ctx = ctx or _ctx
    ctx.logger.info('Initializing GCP Account Info')
    ctx.logger.info('Checking for these locations: {r}.'.format(r=zones))
    resource_types = resource_config.get('resource_types', [])
    ctx.logger.info('Checking for these resource types: {t}.'.format(
        t=resource_types))
    zones = zones or get_zones()
    ctx.instance.runtime_properties['resources'] = get_resources(
        ctx.node, zones, resource_types, ctx.logger)


@operation
def deinitialize(ctx, **_):
    """Delete the resources runtime property. """
    ctx = ctx or _ctx
    del ctx.instance.runtime_properties['resources']


def get_resources(node, zones, resource_types, logger):
    """Get a dict of resources in the following structure:

    :param node: ctx.node
    :param zones: list of GCP zones, i.e. asia-east1-a
    :param resource_types: List of resource types,
        i.e. projects.zones.clusters.
    :param logger: ctx logger
    :return: a dictionary of resources in the structure:
        {
            'projects.zones.clusters': {
                'asia-east1-a': {
                    'resource_id': resource
                }
            }
        }
    """

    logger.info('Checking for these resource types: {t}.'.format(
        t=resource_types))
    resources = {}
    # The structure goes resources.location.resource_type.resource, so we start
    # with location.
    # then resource type.
    for zone in zones:
        logger.info('Checking in this zone: {z}'.format(z=zone))
        for resource_type in resource_types:
            logger.info(
                'Checking for this resource type: {t}.'.format(
                    t=resource_type))
            # Get the class callable, the service name, and resource_id key.
            class_decl, service_name, resource_key = TYPES_MATRIX.get(
                resource_type)
            # Note that the service_name needs to be updated in the Cloudify
            # GCP plugin resource module class for supporting new types.
            if not class_decl:
                # It means that we don't support whatever they provided.
                raise NonRecoverableError(
                    'Unsupported resource type: {t}.'.format(t=resource_type))
            iface = get_resource_interface(node, zone, class_decl, logger)
            # Get the resource response from the API.
            # Clean it up for context serialization.
            # Add this stuff to the resources dict.
            for resource in iface.list():
                resource_id = resource[resource_key]
                resource_entry = {resource_id: resource}
                if zone not in resources:
                    resources[zone] = {
                        resource_type: resource_entry
                    }
                elif resource_type not in resources[resource['location']]:
                    resources[zone][resource_type] = resource_entry
                else:
                    resources[zone][resource_type][resource_id] = resource
    return resources


def get_resource_interface(node, zone, class_decl, logger):
    if not isinstance(node, NodeContext):
        node.properties['client_config'] = desecretize_client_config(
            node.properties['client_config'])
    gcp_config = utils.get_gcp_config(node, requested_zone=zone)
    return class_decl(gcp_config, logger, 'foo')


def get_zones(*_, **__):
    return ['asia-east1-a',
            'asia-east1-b',
            'asia-east1-c',
            'asia-east2-a',
            'asia-east2-b',
            'asia-east2-c',
            'asia-northeast1-a',
            'asia-northeast1-b',
            'asia-northeast1-c',
            'asia-northeast2-a',
            'asia-northeast2-b',
            'asia-northeast2-c',
            'asia-northeast3-a',
            'asia-northeast3-b',
            'asia-northeast3-c',
            'asia-south1-a',
            'asia-south1-b',
            'asia-south1-c',
            'asia-south2-a',
            'asia-south2-b',
            'asia-south2-c',
            'asia-southeast1-a',
            'asia-southeast1-b',
            'asia-southeast1-c',
            'asia-southeast2-a',
            'asia-southeast2-b',
            'asia-southeast2-c',
            'australia-southeast1-a',
            'australia-southeast1-b',
            'australia-southeast1-c',
            'australia-southeast2-a',
            'australia-southeast2-b',
            'australia-southeast2-c',
            'europe-central2-a',
            'europe-central2-b',
            'europe-central2-c',
            'europe-north1-a',
            'europe-north1-b',
            'europe-north1-c',
            'europe-west1-b',
            'europe-west1-c',
            'europe-west1-d',
            'europe-west2-a',
            'europe-west2-b',
            'europe-west2-c',
            'europe-west3-a',
            'europe-west3-b',
            'europe-west3-c',
            'europe-west4-a',
            'europe-west4-b',
            'europe-west4-c',
            'europe-west6-a',
            'europe-west6-b',
            'europe-west6-c',
            'northamerica-northeast1-a',
            'northamerica-northeast1-b',
            'northamerica-northeast1-c',
            'northamerica-northeast2-a',
            'northamerica-northeast2-b',
            'northamerica-northeast2-c',
            'southamerica-east1-a',
            'southamerica-east1-b',
            'southamerica-east1-c',
            'us-central1-a',
            'us-central1-b',
            'us-central1-c',
            'us-central1-f',
            'us-east1-b',
            'us-east1-c',
            'us-east1-d',
            'us-east4-a',
            'us-east4-b',
            'us-east4-c',
            'us-west1-a',
            'us-west1-b',
            'us-west1-c',
            'us-west2-a',
            'us-west2-b',
            'us-west2-c',
            'us-west3-a',
            'us-west3-b',
            'us-west3-c',
            'us-west4-a',
            'us-west4-b',
            'us-west4-c'
            ]
