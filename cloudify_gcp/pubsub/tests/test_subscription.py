# -*- coding: utf-8 -*-
########
# Copyright (c) 2018-2020 Cloudify Platform Ltd. All rights reserved
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

# Local imports
from __future__ import unicode_literals

# Third-party imports
from mock import patch

# Local imports
from .. import subscription
from ...tests import TestGCP


@patch('cloudify_gcp.utils.assure_resource_id_correct', return_value=True)
@patch('cloudify_gcp.gcp.service_account.Credentials.'
       'from_service_account_info')
@patch('cloudify_gcp.utils.get_gcp_resource_name', return_value='valid_name')
@patch('cloudify_gcp.gcp.build')
class TestGCPSubscription(TestGCP):

    def test_create(self, mock_build, *args):
        subscription.create('topic-1', 'valid_name', )

        mock_build().projects().subscriptions(
        ).create.assert_called_once_with(
            body={'topic': 'projects/not really a project/topics/topic-1',
                  'pushConfig': {}},
            name='projects/not really a project/subscriptions/valid_name')

    def test_delete(self, mock_build, *args):
        self.ctxmock.instance.runtime_properties['name'] = 'valid_name'
        self.ctxmock.instance.runtime_properties['topic'] = 'topic-1'
        subscription.delete()
        mock_build.assert_called_once()
