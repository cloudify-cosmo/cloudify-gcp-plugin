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
from setuptools import setup


def read(rel_path):
    here = os.path.abspath(os.path.dirname(__file__))
    with open(os.path.join(here, rel_path), 'r') as fp:
        return fp.read()


def get_version(rel_file):
    lines = read(rel_file)
    for line in lines.splitlines():
        if 'package_version' in line:
            split_line = line.split(':')
            line_no_space = split_line[-1].replace(' ', '')
            line_no_quotes = line_no_space.replace('\'', '')
            return line_no_quotes.strip('\n')
    raise RuntimeError('Unable to find version string.')


setup(
    name='cloudify-gcp-plugin',
    version=get_version('plugin.yaml'),
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
        "cloudify-common>=4.5.5",
        "pyyaml==3.12",
        "pycrypto==2.6.1",
        "jsonschema==3.0.0",
        "httplib2==0.17.3",
    ],
)
