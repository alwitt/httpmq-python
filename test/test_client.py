"""Test bench for httpmq.client"""

# pylint: disable=too-few-public-methods

import logging
import uuid
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
        self.expected_result = None
        self.echo_request_body_in_response = False

    def reset(self):
        """Reset the dummy server"""
        self.expected_status = 200
        self.expected_result = None
        self.echo_request_body_in_response = False

    async def echo_handler(self, request: web.Request):
        """Echo back the parameters, headers, and payload received"""
        all_queries = request.query
        all_headers = request.headers
        # combine the header and query parameters together
        response_header = CIMultiDict()
        response_header.extend(all_queries)
        response_header.extend(all_headers)
        return web.Response(
            status=self.expected_status,
            headers=response_header,
            body=(
                self.expected_result
                if not self.echo_request_body_in_response
                else await request.read()
            ),
        )


class TestAPIClient(AioHTTPTestCase):
    """Test bench for httpmq.client.APIClient"""

    @classmethod
    def setUpClass(cls):
        """To be called for all test cases"""
        cls.test_handler = DummyServer()
        httpmq.configure_sdk_logging(global_log_level=logging.DEBUG)

    async def get_application(self) -> web.Application:
        """Return custom test server"""
        self.test_handler.reset()
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

    async def test_get(self):
        """Verify APIClient.get"""

        test_server = self.server

        # Check GET on the ready end-point of httpmq management APIs
        base_url = f"http://{test_server.host}:{test_server.port}"

        uut = APIClient(base_url=base_url)

        # Case 0: test basic operation
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

        # Case 1: test error code
        self.test_handler.expected_status = 500
        context = RequestContext()
        response = await uut.get(path="/test", ctxt=context)
        self.assertEqual(500, response.status)
        self.assertEqual(
            set(response.headers.getall(httpmq.DEFAULT_REQUEST_ID_FIELD)),
            {context.request_id},
        )

        # Case 2: test response payload
        self.test_handler.expected_status = 200
        test_msg = str(uuid.uuid4()).encode("utf-8")
        self.test_handler.expected_result = test_msg
        context = RequestContext()
        response = await uut.get(path="/test", ctxt=context)
        self.assertEqual(200, response.status)
        self.assertEqual(
            set(response.headers.getall(httpmq.DEFAULT_REQUEST_ID_FIELD)),
            {context.request_id},
        )
        self.assertEqual(response.content, test_msg)

    async def test_post(self):
        """Verify APIClient.post"""

        test_server = self.server

        # Check GET on the ready end-point of httpmq management APIs
        base_url = f"http://{test_server.host}:{test_server.port}"

        uut = APIClient(base_url=base_url)

        # Case 0: test basic operation
        param_1 = str(uuid.uuid4())
        header_1 = str(uuid.uuid4())
        header_2 = str(uuid.uuid4())
        context = (
            RequestContext()
            .add_header("hello", header_1)
            .add_header("hello", header_2)
            .add_param("checking", param_1)
        )
        response = await uut.post(path="/test", ctxt=context, body=None)
        self.assertEqual(200, response.status)
        self.assertEqual(set(response.headers.getall("checking")), {param_1})
        self.assertEqual(set(response.headers.getall("hello")), {header_1, header_2})
        self.assertEqual(
            set(response.headers.getall(httpmq.DEFAULT_REQUEST_ID_FIELD)),
            {context.request_id},
        )

        # Case 1: test request payload
        self.test_handler.echo_request_body_in_response = True
        test_msg = str(uuid.uuid4()).encode("utf-8")
        context = RequestContext()
        response = await uut.post(path="/test", ctxt=context, body=test_msg)
        self.assertEqual(
            set(response.headers.getall(httpmq.DEFAULT_REQUEST_ID_FIELD)),
            {context.request_id},
        )
        self.assertEqual(response.content, test_msg)

        # Case 2: test error code
        self.test_handler.expected_status = 400
        context = RequestContext()
        response = await uut.post(path="/test", ctxt=context, body=test_msg)
        self.assertEqual(400, response.status)
        self.assertEqual(
            set(response.headers.getall(httpmq.DEFAULT_REQUEST_ID_FIELD)),
            {context.request_id},
        )

    async def test_put(self):
        """Verify APIClient.put"""

        test_server = self.server

        # Check GET on the ready end-point of httpmq management APIs
        base_url = f"http://{test_server.host}:{test_server.port}"

        uut = APIClient(base_url=base_url)

        # Case 0: test basic operation
        param_1 = str(uuid.uuid4())
        header_1 = str(uuid.uuid4())
        header_2 = str(uuid.uuid4())
        context = (
            RequestContext()
            .add_header("hello", header_1)
            .add_header("hello", header_2)
            .add_param("checking", param_1)
        )
        response = await uut.put(path="/test", ctxt=context, body=None)
        self.assertEqual(200, response.status)
        self.assertEqual(set(response.headers.getall("checking")), {param_1})
        self.assertEqual(set(response.headers.getall("hello")), {header_1, header_2})
        self.assertEqual(
            set(response.headers.getall(httpmq.DEFAULT_REQUEST_ID_FIELD)),
            {context.request_id},
        )

        # Case 1: test request payload
        self.test_handler.echo_request_body_in_response = True
        test_msg = str(uuid.uuid4()).encode("utf-8")
        context = RequestContext()
        response = await uut.put(path="/test", ctxt=context, body=test_msg)
        self.assertEqual(
            set(response.headers.getall(httpmq.DEFAULT_REQUEST_ID_FIELD)),
            {context.request_id},
        )
        self.assertEqual(response.content, test_msg)

        # Case 2: test error code
        self.test_handler.expected_status = 400
        context = RequestContext()
        response = await uut.put(path="/test", ctxt=context, body=test_msg)
        self.assertEqual(400, response.status)
        self.assertEqual(
            set(response.headers.getall(httpmq.DEFAULT_REQUEST_ID_FIELD)),
            {context.request_id},
        )
