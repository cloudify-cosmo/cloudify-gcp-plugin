# #######
# Copyright (c) 2016-2020 Cloudify Platform Ltd. All rights reserved
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

import pytest
from mock import patch, PropertyMock

from .. import address


@pytest.fixture(autouse=True)
def patch_zones():
    with patch(
            'cloudify_gcp.gcp.GoogleCloudPlatform.ZONES',
            new_callable=PropertyMock,
            return_value={
                'a very fake zone': {
                    'region_name': 'expected region name',
                },
            },
    ):
        yield


@patch('cloudify_gcp.gcp.build')
@pytest.mark.parametrize(
    'region, node_type, section', [
        ('region', 'cloudify.gcp.nodes.Address', 'addresses'),
        (None, 'cloudify.gcp.nodes.Address', 'addresses'),
        (None, 'cloudify.gcp.nodes.GlobalAddress', 'globalAddresses'),
    ],
)
def test_create(mock_build, region=None, node_type=None, section=None,
                ctx=None):
    if not ctx:
        ctx = mock_build()
    ctx.node.type_hierarchy = [node_type]

    address.create(
        'name',
        additional_settings={},
        region=region,
    )

    expected = {
        'body': {
            'description': 'Cloudify generated Address',
            'name': 'name',
        },
        'project': 'not really a project',
    }
    if region:
        expected['region'] = 'region'
    elif section == 'addresses':
        expected['region'] = 'expected region name'

    getattr(mock_build(), section)().insert.assert_called_once_with(**expected)


@patch('cloudify_gcp.gcp.build')
@pytest.mark.parametrize(
    'node_type, section', [
        ('cloudify.gcp.nodes.Address', 'addresses'),
        ('cloudify.gcp.nodes.GlobalAddress', 'globalAddresses'),
    ],
)
def test_delete(mock_build, node_type=None, section=None, ctx=None):
    ctx.node.type_hierarchy = [node_type]
    ctx.instance.runtime_properties.update({
        'gcp_name': 'delete me',
        'region': 'Costa Del Sol',
        'name': 'delete me',
    })

    address.delete()

    expected = dict(
        project='not really a project',
        address='delete me',
    )
    if section == 'addresses':
        expected['region'] = 'Costa Del Sol'

    getattr(mock_build(), section)().delete.assert_called_once_with(
        **expected
    )
