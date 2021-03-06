########
# Copyright (c) 2014-2019 Cloudify Platform Ltd. All rights reserved
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
import pytest

from ecosystem_tests.dorkl import (
    basic_blueprint_test,
    cleanup_on_failure, prepare_test
)


SECRETS_TO_CREATE = {
    'gcp_credentials': True
}

prepare_test(secrets=SECRETS_TO_CREATE)

# Temporary until kubernetes plugin will be released with py2py3 wagon.
blueprint_list = [
    'examples/blueprint-examples/kubernetes/gcp-gke/blueprint.yaml',
    'examples/blueprint-examples/virtual-machine/gcp.yaml']


@pytest.fixture(scope='function', params=blueprint_list)
def blueprint_examples(request):
    dirname_param = os.path.dirname(request.param).split('/')[-1:][0]
    try:
        if dirname_param == "gcp-gke":
            inputs = "resource_prefix=gcpresource-{0}"
        else:  # it`s virtual-machine example
            inputs = ''
        basic_blueprint_test(
            request.param, dirname_param,
            inputs=inputs.format(os.environ['CIRCLE_BUILD_NUM']), timeout=3000)
    except:
        cleanup_on_failure(dirname_param)
        raise



def test_blueprints(blueprint_examples):
    assert blueprint_examples is None