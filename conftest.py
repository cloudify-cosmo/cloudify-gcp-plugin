########
# Copyright (c) 2017 GigaSpaces Technologies Ltd. All rights reserved
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
from mock import patch

from cloudify.state import current_ctx

from cloudify_gcp.tests import ctx_mock


@pytest.fixture
def ctx():
    ctxmock = ctx_mock()
    current_ctx.set(ctxmock)

    yield ctxmock

    current_ctx.clear()


@pytest.fixture(autouse=True)
def patch_client():
    with patch(
            'cloudify_gcp.gcp.ServiceAccountCredentials.from_json_keyfile_dict'
            ):
        yield
