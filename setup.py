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


from setuptools import setup

setup(

    name='cloudify-gcp-plugin',

    version='1.6.3',
    description='Plugin for Google Cloud Platform',

    packages=[
        'cloudify_gcp.admin',
        'cloudify_gcp',
        'cloudify_gcp.compute',
        'cloudify_gcp.monitoring',
        'cloudify_gcp.container_engine',
        'cloudify_gcp.logging',
        'cloudify_gcp.dns',
    ],

    license='LICENSE',
    zip_safe=False,
    install_requires=[
        "oauth2client==4.1.3",
        "google-api-python-client==1.7.11",
        "cloudify-common>=4.4.0",
        "pyyaml",
        "pycrypto",
        "jsonschema==3.0.0",
        "httplib2"
    ],
)
