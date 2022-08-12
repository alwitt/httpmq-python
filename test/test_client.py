"""Test bench for httpmq.client"""

from test import BaseTestCase, async_test, get_unittest_httpmq_mgmt_api_url
from httpmq.client import APIClient
from httpmq.common import RequestContext


class TestAPIClient(BaseTestCase):
    """Test bench for httpmq.client.APIClient"""

    @async_test
    async def test_basic_sanity(self):
        """Verify basic function of APIClient"""

        # Check GET on the ready end-point of httpmq management APIs
        base_url = get_unittest_httpmq_mgmt_api_url()

        uut = APIClient(base_url=base_url)

        context = (
            RequestContext()
            .add_header("hello", "world")
            .add_header("hello", "again")
            .add_param("checking", "1")
        )
        response = await uut.get(path="/v1/admin/ready", ctxt=context)

        self.assertEqual(200, response.status)
