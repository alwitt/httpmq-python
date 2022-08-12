"""Test bench for httpmq.client"""

# pylint: disable=too-few-public-methods

import logging
from aiohttp import web
from aiohttp.test_utils import AioHTTPTestCase
from multidict import CIMultiDict
import httpmq
from httpmq.client import APIClient
from httpmq.common import RequestContext


class DummyServer:
    """Test server used to the API client"""

    def __init__(self):
        """Constructor"""
        self.expected_status = 200

    async def echo_handler(self, request: web.Request):
        """Echo back the parameters, headers, and payload received"""
        all_queries = request.query
        all_headers = request.headers
        # combine the header and query parameters together
        response_header = CIMultiDict()
        response_header.extend(all_queries)
        response_header.extend(all_headers)
        return web.Response(status=self.expected_status, headers=response_header)


class TestAPIClient(AioHTTPTestCase):
    """Test bench for httpmq.client.APIClient"""

    @classmethod
    def setUpClass(cls):
        """To be called for all test cases"""
        cls.test_handler = DummyServer()
        httpmq.configure_sdk_logging(global_log_level=logging.DEBUG)

    async def get_application(self) -> web.Application:
        """Return custom test server"""
        app = web.Application()
        app.router.add_routes(
            [
                web.get("/test", self.test_handler.echo_handler),
                web.put("/test", self.test_handler.echo_handler),
                web.post("/test", self.test_handler.echo_handler),
                web.delete("/test", self.test_handler.echo_handler),
            ]
        )
        return app

    async def test_basic_sanity(self):
        """Verify basic function of APIClient"""

        test_server = self.server

        # Check GET on the ready end-point of httpmq management APIs
        base_url = f"http://{test_server.host}:{test_server.port}"

        uut = APIClient(base_url=base_url)

        context = (
            RequestContext()
            .add_header("hello", "world")
            .add_header("hello", "again")
            .add_param("checking", "1")
        )
        response = await uut.get(path="/test", ctxt=context)

        self.assertEqual(200, response.status)
        self.assertEqual(set(response.headers.getall("checking")), {"1"})
        self.assertEqual(set(response.headers.getall("hello")), {"world", "again"})
        self.assertEqual(
            set(response.headers.getall(httpmq.DEFAULT_REQUEST_ID_FIELD)),
            {context.request_id},
        )

        self.test_handler.expected_status = 500
        context = RequestContext()
        response = await uut.get(path="/test", ctxt=context)
        self.assertEqual(500, response.status)
        self.assertEqual(
            set(response.headers.getall(httpmq.DEFAULT_REQUEST_ID_FIELD)),
            {context.request_id},
        )
