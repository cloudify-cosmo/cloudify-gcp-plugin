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


from setuptools import setup

setup(

    name='cloudify-gcp-plugin',

    version='0.1',
    description='Plugin for Google Cloud Platform',

    packages=['gcp', 'gcp/compute'],

    license='LICENSE',
    zip_safe=False,
    install_requires=[
        "cloudify-plugins-common==3.3",
        "oauth2client==1.4.6",
        "google-api-python-client==1.4.0",
        "pyyaml",
        "Crypto"
    ],
    test_requires=[
        "cloudify-dsl-parser==3.2   ",
        "nose"
    ]
)
