"""Test bench for httpmq.dataplane"""

import aiohttp
from httpmq.client import APIClient
from httpmq.common import RequestContext
from httpmq.dataplane import DataAPIWrapper
from . import BaseTestCase, async_test, get_unittest_httpmq_data_api_url


class TestDataplane(BaseTestCase):
    """Test bench for httpmq.dataplane"""

    @async_test
    async def test_basic_sanity(self):
        """Basic sanity check of management API client"""

        core_client = APIClient(base_url=get_unittest_httpmq_data_api_url())
        mgmt_client = DataAPIWrapper(api_client=core_client)
        await mgmt_client.ready(context=RequestContext())

        another_client = APIClient(base_url="http://127.0.0.1:17881")
        another_mgmt_client = DataAPIWrapper(api_client=another_client)
        with self.assertRaises(aiohttp.client_exceptions.ClientConnectorError):
            await another_mgmt_client.ready(context=RequestContext())
