# -*- coding: utf-8 -*-
########
# Copyright (c) 2017-2020 Cloudify Platform Ltd. All rights reserved
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
import mock

# Local imports
from cloudify.exceptions import NonRecoverableError

from cloudify_gcp.container_engine import cluster
from ...tests import TestGCP


@patch('cloudify_gcp.utils.assure_resource_id_correct', return_value=True)
@patch('cloudify_gcp.gcp.ServiceAccountCredentials.from_json_keyfile_dict')
@patch('cloudify_gcp.utils.get_gcp_resource_name', return_value='valid_name')
@patch('cloudify_gcp.gcp.build')
class TestGCPCluster(TestGCP):

    def test_create(self, mock_build, *args):
        cluster.create('valid_name', additional_settings={}, )

        mock_build().projects().zones().clusters(

        ).create.assert_called_once_with(
                body={'cluster': {'name': 'valid_name',
                                  'initialNodeCount': 1}, },
                projectId='not really a project',
                zone='a very fake zone')

    def test_start(self, mock_build, *args):
        self.ctxmock.instance.runtime_properties['name'] = 'valid_name'

        clusters = mock_build().projects().zones().clusters().get().execute()

        # started
        clusters.get = mock.Mock(
            return_value=cluster.constants.KUBERNETES_RUNNING_STATUS)
        cluster.start()

        # reconciling
        clusters.get = mock.Mock(
            return_value=cluster.constants.KUBERNETES_RECONCILING_STATUS)
        cluster.start()

        # provisioning
        self.ctxmock.operation.retry = mock.Mock()
        clusters.get = mock.Mock(
            return_value=cluster.constants.KUBERNETES_PROVISIONING_STATUS)
        cluster.start()
        self.ctxmock.operation.retry.assert_called_with(
            'Kubernetes resource is still provisioning.', 15)

        # provisioning
        self.ctxmock.operation.retry = mock.Mock()
        clusters.get = mock.Mock(
            return_value=cluster.constants.KUBERNETES_ERROR_STATUS)
        with self.assertRaises(NonRecoverableError):
            cluster.start()

        # unknow
        self.ctxmock.operation.retry = mock.Mock()
        clusters.get = mock.Mock(return_value='unknow')
        cluster.start()

    def test_delete(self, mock_build, *args):
        self.ctxmock.instance.runtime_properties['name'] = 'valid_name'

        clusters = mock_build().projects().zones().clusters().get().execute()

        # stopping
        self.ctxmock.operation.retry = mock.Mock()
        clusters.get = mock.Mock(
            return_value=cluster.constants.KUBERNETES_STOPPING_STATUS)
        cluster.delete()
        self.ctxmock.operation.retry.assert_called_with(
            'Kubernetes resource is still de-provisioning')

        # error
        self.ctxmock.operation.retry = mock.Mock()
        clusters.get = mock.Mock(
            return_value=cluster.constants.KUBERNETES_ERROR_STATUS)
        with self.assertRaises(NonRecoverableError):
            cluster.delete()

    def test_stop(self, mock_build, *args):
        self.ctxmock.instance.runtime_properties['name'] = 'valid_name'

        cluster.stop()

        mock_build.assert_called_once()

        mock_build().projects().zones().clusters().delete.assert_called_with(
            clusterId='valid_name',
            projectId='not really a project',
            zone='a very fake zone')
