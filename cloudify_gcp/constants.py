########
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
import os.path

MAX_GCP_NAME = 63
ID_HASH_CONST = 6

COMPUTE_SCOPE = 'https://www.googleapis.com/auth/compute'
MONITORING_SCOPE = 'https://www.googleapis.com/auth/monitoring'
STORAGE_SCOPE_RW = 'https://www.googleapis.com/auth/devstorage.read_write'
STORAGE_SCOPE_FULL = 'https://www.googleapis.com/auth/devstorage.full_control'
CONTAINER_SCOPE = 'https://www.googleapis.com/auth/cloud-platform'
PUB_SUB_SCOPE = 'https://www.googleapis.com/auth/pubsub'
LOGGING_SCOPE = 'https://www.googleapis.com/auth/logging.admin'

COMPUTE_DISCOVERY = 'compute'
STORAGE_DISCOVERY = 'storage'
CONTAINER_DISCOVERY = 'container'
MONITORING_DISCOVERY = 'monitoring'
PUB_SUB_DISCOVERY = 'pubsub'
LOGGING_DISCOVERY = 'logging'
CLOUDRESOURCES_DISCOVERY = 'cloudresourcemanager'

CHUNKSIZE = 2 * 1024 * 1024

API_V1 = 'v1'
API_V2 = 'v2'
API_V3 = 'v3'
API_BETA = 'beta'

DISK = 'gcp_disk'
KUBERNETES_CLUSTER = 'gcp_kubernetes_cluster'
KUBERNETES_NODE_POOL = 'gcp_kubernetes_node_pool'
KUBERNETES_READY_STATUS = 'READY'
KUBERNETES_RUNNING_STATUS = 'RUNNING'
KUBERNETES_RECONCILING_STATUS = 'RECONCILING'
KUBERNETES_PROVISIONING_STATUS = 'PROVISIONING'
KUBERNETES_STOPPING_STATUS = 'STOPPING'
KUBERNETES_ERROR_STATUS = 'ERROR'
GCP_ZONE = 'gcp_zone'
HEALTH_CHECK_TYPE = 'gcp_health_check_type'
TARGET_PROXY_TYPE = 'gcp_target_proxy_type'
BACKENDS = 'gcp_backends'
IP = 'gcp_ip'
SELF_URL = 'selfLink'
ID = 'id'
TARGET_TAGS = 'targetTags'
SOURCE_TAGS = 'sourceTags'
PUBLIC_KEY = 'gcp_public_key'
PRIVATE_KEY = 'gcp_private_key'
USER = 'user'
SSH_KEYS = 'ssh_keys'
MANAGEMENT_SECURITY_GROUP = 'management_security_group'
MANAGER_AGENT_SECURITY_GROUP = 'manager_agent_security_group'
AGENTS_SECURITY_GROUP = 'agents_security_group'
SECURITY_GROUPS = [MANAGEMENT_SECURITY_GROUP,
                   MANAGER_AGENT_SECURITY_GROUP,
                   AGENTS_SECURITY_GROUP]
USE_EXTERNAL_RESOURCE = 'use_external_resource'
RESOURCE_ID = 'resource_id'

GCP_CONFIG = 'gcp_config'
AUTH = 'auth'
PROJECT = 'project'
ZONE = 'zone'
NETWORK = 'network'
NAME = 'name'

GCP_OP_DONE = 'DONE'

MANAGER_PLUGIN_FILES = os.path.join('/etc', 'cloudify', 'gcp_plugin')
GCP_DEFAULT_CONFIG_PATH = os.path.join(MANAGER_PLUGIN_FILES, 'gcp_config')

RETRY_DEFAULT_DELAY = 30

# Cloudify create node action
CREATE_NODE_ACTION = "cloudify.interfaces.lifecycle.create"
# Cloudify delete node action
DELETE_NODE_ACTION = "cloudify.interfaces.lifecycle.delete"

GCP_CREDENTIALS_SCHEMA = {
    "type": "object",
    "properties": {
        "type": {"type": "string"},
        "project_id": {"type": "string"},
        "private_key_id": {"type": "string"},
        "private_key": {"type": "string"},
        "client_email": {"type": "string"},
        "client_id": {"type": "string"},
        "auth_uri": {"type": "string"},
        "token_uri": {"type": "string"},
        "auth_provider_x509_cert_url": {"type": "string"},
        "client_x509_cert_url": {"type": "string"},

    },
    "required": ["type", "project_id", "private_key_id", "private_key",
                 "client_email", "client_id", "auth_uri",
                 "token_uri", "auth_provider_x509_cert_url",
                 "client_x509_cert_url"],
    "additionalProperties": False
}
