
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
