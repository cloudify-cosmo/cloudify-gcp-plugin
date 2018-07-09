# Built-in Imports
import os

# Cloudify Imports
from ecosystem_tests import EcosystemTestBase, utils


GCLOUD_COMPUTE_COMMAND = 'gcloud compute {0} describe {1}'

CFY_GCP_COMPUTE_RESOURCE = {
    'nodecellar.nodes.MonitoredServer': 'instances',
    'cloudify.gcp.nodes.Instance': 'instances',
    'cloudify.gcp.nodes.FirewallRule': 'firewall-rules',
    'cloudify.gcp.nodes.SubNetwork': 'networks subnets',
    'cloudify.gcp.nodes.Network': 'networks',
}

CFY_NODES_PATTERNS = ['cloudify.gcp.nodes', 'nodecellar.nodes']


class TestGCP(EcosystemTestBase):

    @property
    def node_type_prefix(self):
        return 'cloudify.gcp.nodes'

    @property
    def plugin_mapping(self):
        return 'gcp_plugin'

    @property
    def blueprint_file_name(self):
        return 'gcp.yaml'

    @property
    def external_id_key(self):
        return 'resource_id'

    @property
    def server_ip_property(self):
        return 'natIP'

    @property
    def plugins_to_upload(self):
        return []

    @property
    def inputs(self):
        try:
            return {
                'password': os.environ['ECOSYSTEM_SESSION_PASSWORD'],
                'client_x509_cert_url': os.environ['GCP_CERT_URL'],
                'client_email': os.environ['GCP_EMAIL'],
                'client_id': os.environ['GCP_CLIENT_ID'],
                'project_id': os.environ['GCP_PRIVATE_PROJECT_ID'],
                'private_key_id': os.environ['GCP_PRIVATE_KEY_ID'],
                'private_key':
                    os.environ['GCP_PRIVATE_KEY'].decode('string_escape'),
                'zone': 'us-east1-b',
                'region': 'us-east1',
            }
        except KeyError:
            raise

    @property
    def sensitive_data(self):
        return [
            os.environ['GCP_PRIVATE_PROJECT_ID'],
            os.environ['GCP_PRIVATE_KEY_ID'],
            os.environ['GCP_CLIENT_ID'],
            os.environ['GCP_EMAIL'],
        ]

    def get_manager_ip(self, manager_node='cloudify_host'):
        for instance in self.node_instances:
            if instance.node_id == manager_node:
                # Return Public ip for gcp  cloudify host manager
                return instance.runtime_properties[
                    'networkInterfaces'][0]['accessConfigs'][0][
                    self.server_ip_property]
        raise Exception('No manager IP found.')

    def get_resources_from_deployment(self, deployment_id, node_type,):

        return utils.get_deployment_resources_by_node_type_substring(
            deployment_id, node_type,)

    def check_resource_method(self, resources=None, name_property='name'):
        if resources:
            for resource in resources:
                node_type = resource['node_type']
                # if it exists then the prefix command should be
                # "gcloud compute"
                # otherwise the prefix command should be something else
                if CFY_GCP_COMPUTE_RESOURCE.get(node_type):
                    gcp_resource = CFY_GCP_COMPUTE_RESOURCE[node_type]

                    # Get the name of the resource for the current node from
                    # the created instances associated with it
                    for instance in resource['instances']:
                        # Get the name form the "runtime_properties"
                        name =\
                            instance['runtime_properties'].get(name_property)
                        describe_resource =\
                            GCLOUD_COMPUTE_COMMAND.format(gcp_resource, name)
                        self.assertEqual(
                            0, utils.execute_command(describe_resource))

    def check_nodecellar(self):
        nc_inputs = {
            'resource_prefix':
                'cfy-nc-{0}'.format(os.environ['CIRCLE_BUILD_NUM'])
        }
        # Add Cleanup method to clean "nc" whenever tests fail or pass
        self.addCleanup(self.cleanup_deployment, 'nc')

        # Check if executing install workflow passed or not
        if utils.install_nodecellar(
                blueprint_file_name=self.blueprint_file_name,
                inputs=nc_inputs) != 0:
            raise Exception('nodecellar install failed.')

        # Check if executing scale workflow passed or not
        utils.execute_scale('nc')

        for node_type in CFY_NODES_PATTERNS:
            nc_resources = self.get_resources_from_deployment('nc', node_type)
            self.check_resource_method(nc_resources)

    def test_install_network(self):
        network_inputs = {
            'resource_suffix': os.environ['CIRCLE_BUILD_NUM']
        }
        # Add Cleanup method to clean "gcp-example-network" whenever tests
        # fail or pass
        self.addCleanup(self.cleanup_deployment, 'gcp-example-network')

        # Check if creating deployment passed or not
        if utils.create_deployment('gcp-example-network',
                                   inputs=network_inputs):
            raise Exception(
                'Deployment gcp-example-network failed.')

        # Check if executing install workflow passed or not
        if utils.execute_install('gcp-example-network'):
            raise Exception(
                'Install aws-example-network failed.')

        gcp_network_resources =\
            self.get_resources_from_deployment('gcp-example-network',
                                               self.node_type_prefix)

        self.check_resource_method(gcp_network_resources)

        self.check_nodecellar()
