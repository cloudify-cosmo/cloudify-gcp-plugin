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
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


from setuptools import setup

setup(

    name='cloudify-gcp-plugin',

    version='1.4.3',
    description='Plugin for Google Cloud Platform',

    packages=[
        'cloudify_gcp.admin',
        'cloudify_gcp',
        'cloudify_gcp.compute',
        'cloudify_gcp.container_engine',
        'cloudify_gcp.dns',
        ],

    license='LICENSE',
    zip_safe=False,
    install_requires=[
        "oauth2client==3",
        "google-api-python-client==1.5.1",
        "cloudify-plugins-common>=3.3.1",
        "pyyaml",
        "pycrypto",
    ],
)
