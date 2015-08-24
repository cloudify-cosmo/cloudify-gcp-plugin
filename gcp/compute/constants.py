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
#    * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    * See the License for the specific language governing permissions and
#    * limitations under the License.
import os.path

MAX_GCP_NAME = 63
ID_HASH_CONST = 6

COMPUTE_SCOPE = 'https://www.googleapis.com/auth/compute'
STORAGE_SCOPE_RW = 'https://www.googleapis.com/auth/devstorage.read_write'
STORAGE_SCOPE_FULL = 'https://www.googleapis.com/auth/devstorage.full_control'

COMPUTE_DISCOVERY = 'compute'
STORAGE_DISCOVERY = 'storage'

CHUNKSIZE = 2 * 1024 * 1024

NAME = 'gcp_name'
DISK = 'gcp_disk'
ID = 'id'
TARGET_TAGS = 'targetTags'
SOURCE_TAGS = 'sourceTags'
PUBLIC_KEY = 'gcp_public_key'
PRIVATE_KEY = 'gcp_private_key'
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

MANAGER_HOMEDIR = os.path.join(os.sep, 'tmp', 'home')
GCP_DEFAULT_CONFIG_PATH = os.path.join(MANAGER_HOMEDIR, 'gcp_config.json')

RETRY_DEFAULT_DELAY = 30
