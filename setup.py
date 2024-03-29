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

import os
import re
import sys
import pathlib
from setuptools import setup, find_packages


def get_version():
    current_dir = pathlib.Path(__file__).parent.resolve()
    with open(os.path.join(
            current_dir,
            'cloudify_gcp/__version__.py'), 'r') as outfile:
        var = outfile.read()
        return re.search(r'\d+.\d+.\d+', var).group()


install_requires = [
    'oauth2client==4.1.3',
    'google-auth==2.15.0',
    'jsonschema==3.0.0',
    'httplib2>=0.18.0'
]


if sys.version_info.major == 3 and sys.version_info.minor == 6:
    install_requires += [
        'google-api-python-client>=2.52.0',
        'cloudify-common>=6.3.1,<7.0',
        'cloudify-utilities-plugins-sdk>=0.0.124',
    ]
    packages = [
        'cloudify_gcp.admin',
        'cloudify_gcp',
        'cloudify_gcp.compute',
        'cloudify_gcp.monitoring',
        'cloudify_gcp.container_engine',
        'cloudify_gcp.logging',
        'cloudify_gcp.dns',
        'cloudify_gcp.iam',
        'cloudify_gcp.workflows',
    ]
else:
    install_requires += [
        'google-api-python-client>=2.92.0',
        'fusion-common',
        'cloudify-utilities-plugins-sdk',
    ]
    packages = find_packages(exclude=['tests*'])


setup(
    name='cloudify-gcp-plugin',
    version=get_version(),
    description='Plugin for Google Cloud Platform',
    packages=packages,
    license='LICENSE',
    zip_safe=False,
    install_requires=install_requires,
)
