"""Test bench for httpmq.client"""

# pylint: disable=too-few-public-methods
# pylint: disable=attribute-defined-outside-init

import asyncio
import logging
import uuid
from aiohttp import web
from aiohttp.test_utils import AioHTTPTestCase
from multidict import CIMultiDict
import httpmq


class DummyServer:
    """Test server used to the API client"""

    class Message:
        """Wrapper object for passing messages within the message queue"""

        def __init__(self, msg: str):
            """Constructor"""
            self.msg = msg

    class EndMarker:
        """Wrapper object for passing a end marker within the message queue"""

        def __init__(self):
            """Constructor"""
            self.is_end = True

    def __init__(self):
        """Constructor"""
        self.log = logging.getLogger("httpmq-sdk.general")
        self.expected_status = 200
        self.expected_result = None
        self.echo_request_body_in_response = False
        self.msg_queue = asyncio.Queue()

    async def reset(self):
        """Reset the dummy server"""
        self.expected_status = 200
        self.expected_result = None
        self.echo_request_body_in_response = False
        await self.msg_queue.join()

    async def message_handler(self, request: web.Request):
        """Receive and enqueue message from the caller"""
        payload = await request.read()
        payload = payload.decode("utf-8")
        self.log.debug("Dummy server received\n%s", payload)
        if "stop" in request.query:
            self.log.debug("Dummy server sending stop signal to SSE handler")
            await self.msg_queue.put(DummyServer.EndMarker())
        else:
            await self.msg_queue.put(DummyServer.Message(payload))
        return web.Response()

    async def sse_echo_handler(self, request: web.Request):
        """SSE handler which will echo any message received by message_handler"""
        # Drain the request body
        _ = await request.read()
        # Send header out first
        response = web.StreamResponse()
        await response.prepare(request=request)
        self.log.debug("Dummy server SSE handler sent response headers")
        # Start sending out data
        try:
            while True:
                new_msg = await self.msg_queue.get()
                self.msg_queue.task_done()
                if isinstance(new_msg, DummyServer.Message):
                    msg = f"{new_msg.msg.strip()}\n"
                    self.log.debug("Dummy server sending\n%s", msg)
                    await response.write(msg.encode("utf-8"))
                    continue
                # otherwise exit loop
                break
        except OSError:
            pass
        await response.write_eof()
        return response

    async def echo_handler(self, request: web.Request):
        """Echo back the parameters, headers, and payload received"""
        request_body = await request.read()
        all_queries = request.query
        all_headers = request.headers
        # combine the header and query parameters together
        response_header = CIMultiDict()
        response_header.extend(all_queries)
        response_header.extend(all_headers)
        if "Content-Length" in response_header:
            response_header.popall("Content-Length")
        if "Content-Type" in response_header:
            response_header.popall("Content-Type")
        return web.Response(
            status=self.expected_status,
            headers=response_header,
            body=(
                self.expected_result
                if not self.echo_request_body_in_response
                else request_body
            ),
        )


class TestAPIClient(AioHTTPTestCase):
    """Test bench for httpmq.client.APIClient"""

    @classmethod
    def setUpClass(cls):
        """To be called for all test cases"""
        httpmq.configure_sdk_logging(global_log_level=logging.DEBUG)

    async def get_application(self) -> web.Application:
        """Return custom test server"""
        self.test_handler = DummyServer()
        app = web.Application()
        app.router.add_routes(
            [
                web.get("/test", self.test_handler.echo_handler),
                web.put("/test", self.test_handler.echo_handler),
                web.post("/test", self.test_handler.echo_handler),
                web.delete("/test", self.test_handler.echo_handler),
                web.get("/msg", self.test_handler.sse_echo_handler),
                web.post("/msg", self.test_handler.message_handler),
            ]
        )
        return app

    async def test_get(self):
        """Verify APIClient.get"""

        test_server = self.server

        # Check GET on the ready end-point of httpmq management APIs
        base_url = f"http://{test_server.host}:{test_server.port}"

        uut = httpmq.APIClient(base_url=base_url)

        # Case 0: test basic operation
        context = (
            httpmq.RequestContext()
            .add_header("hello", "world")
            .add_header("hello", "again")
            .add_param("checking", "1")
        )
        response = await uut.get(path="/test", context=context)
        self.assertEqual(200, response.status)
        self.assertEqual(set(response.headers.getall("checking")), {"1"})
        self.assertEqual(set(response.headers.getall("hello")), {"world", "again"})
        self.assertEqual(
            set(response.headers.getall(httpmq.common.DEFAULT_REQUEST_ID_FIELD)),
            {context.request_id},
        )

        # Case 1: test error code
        self.test_handler.expected_status = 500
        context = httpmq.RequestContext()
        response = await uut.get(path="/test", context=context)
        self.assertEqual(500, response.status)
        self.assertEqual(
            set(response.headers.getall(httpmq.common.DEFAULT_REQUEST_ID_FIELD)),
            {context.request_id},
        )

        # Case 2: test response payload
        self.test_handler.expected_status = 200
        test_msg = str(uuid.uuid4()).encode("utf-8")
        self.test_handler.expected_result = test_msg
        context = httpmq.RequestContext()
        response = await uut.get(path="/test", context=context)
        self.assertEqual(200, response.status)
        self.assertEqual(
            set(response.headers.getall(httpmq.common.DEFAULT_REQUEST_ID_FIELD)),
            {context.request_id},
        )
        self.assertEqual(response.content, test_msg)

    async def test_post(self):
        """Verify APIClient.post"""

        test_server = self.server

        # Check POST on the ready end-point of httpmq management APIs
        base_url = f"http://{test_server.host}:{test_server.port}"

        uut = httpmq.APIClient(base_url=base_url)

        # Case 0: test basic operation
        param_1 = str(uuid.uuid4())
        header_1 = str(uuid.uuid4())
        header_2 = str(uuid.uuid4())
        context = (
            httpmq.RequestContext()
            .add_header("hello", header_1)
            .add_header("hello", header_2)
            .add_param("checking", param_1)
        )
        response = await uut.post(path="/test", context=context)
        self.assertEqual(200, response.status)
        self.assertEqual(set(response.headers.getall("checking")), {param_1})
        self.assertEqual(set(response.headers.getall("hello")), {header_1, header_2})
        self.assertEqual(
            set(response.headers.getall(httpmq.common.DEFAULT_REQUEST_ID_FIELD)),
            {context.request_id},
        )

        # Case 1: test request payload
        self.test_handler.echo_request_body_in_response = True
        test_msg = str(uuid.uuid4()).encode("utf-8")
        context = httpmq.RequestContext()
        response = await uut.post(path="/test", context=context, body=test_msg)
        self.assertEqual(
            set(response.headers.getall(httpmq.common.DEFAULT_REQUEST_ID_FIELD)),
            {context.request_id},
        )
        self.assertEqual(response.content, test_msg)

        # Case 2: test error code
        self.test_handler.expected_status = 400
        context = httpmq.RequestContext()
        response = await uut.post(path="/test", context=context, body=test_msg)
        self.assertEqual(400, response.status)
        self.assertEqual(
            set(response.headers.getall(httpmq.common.DEFAULT_REQUEST_ID_FIELD)),
            {context.request_id},
        )

    async def test_put(self):
        """Verify APIClient.put"""

        test_server = self.server

        # Check PUT on the ready end-point of httpmq management APIs
        base_url = f"http://{test_server.host}:{test_server.port}"

        uut = httpmq.APIClient(base_url=base_url)

        # Case 0: test basic operation
        param_1 = str(uuid.uuid4())
        header_1 = str(uuid.uuid4())
        header_2 = str(uuid.uuid4())
        context = (
            httpmq.RequestContext()
            .add_header("hello", header_1)
            .add_header("hello", header_2)
            .add_param("checking", param_1)
        )
        response = await uut.put(path="/test", context=context)
        self.assertEqual(200, response.status)
        self.assertEqual(set(response.headers.getall("checking")), {param_1})
        self.assertEqual(set(response.headers.getall("hello")), {header_1, header_2})
        self.assertEqual(
            set(response.headers.getall(httpmq.common.DEFAULT_REQUEST_ID_FIELD)),
            {context.request_id},
        )

        # Case 1: test request payload
        self.test_handler.echo_request_body_in_response = True
        test_msg = str(uuid.uuid4()).encode("utf-8")
        context = httpmq.RequestContext()
        response = await uut.put(path="/test", context=context, body=test_msg)
        self.assertEqual(
            set(response.headers.getall(httpmq.common.DEFAULT_REQUEST_ID_FIELD)),
            {context.request_id},
        )
        self.assertEqual(response.content, test_msg)

        # Case 2: test error code
        self.test_handler.expected_status = 400
        context = httpmq.RequestContext()
        response = await uut.put(path="/test", context=context, body=test_msg)
        self.assertEqual(400, response.status)
        self.assertEqual(
            set(response.headers.getall(httpmq.common.DEFAULT_REQUEST_ID_FIELD)),
            {context.request_id},
        )

    async def test_delete(self):
        """Verify APIClient.delete"""

        test_server = self.server

        # Check DELETE on the ready end-point of httpmq management APIs
        base_url = f"http://{test_server.host}:{test_server.port}"

        uut = httpmq.APIClient(base_url=base_url)

        # Case 0: test basic operation
        context = (
            httpmq.RequestContext()
            .add_header("hello", "world")
            .add_header("hello", "again")
            .add_param("checking", "1")
        )
        response = await uut.delete(path="/test", context=context)
        self.assertEqual(200, response.status)
        self.assertEqual(set(response.headers.getall("checking")), {"1"})
        self.assertEqual(set(response.headers.getall("hello")), {"world", "again"})
        self.assertEqual(
            set(response.headers.getall(httpmq.common.DEFAULT_REQUEST_ID_FIELD)),
            {context.request_id},
        )

        # Case 1: test error code
        self.test_handler.expected_status = 500
        context = httpmq.RequestContext()
        response = await uut.delete(path="/test", context=context)
        self.assertEqual(500, response.status)
        self.assertEqual(
            set(response.headers.getall(httpmq.common.DEFAULT_REQUEST_ID_FIELD)),
            {context.request_id},
        )

        # Case 2: test response payload
        self.test_handler.expected_status = 200
        test_msg = str(uuid.uuid4()).encode("utf-8")
        self.test_handler.expected_result = test_msg
        context = httpmq.RequestContext()
        response = await uut.post(path="/test", context=context)
        self.assertEqual(200, response.status)
        self.assertEqual(
            set(response.headers.getall(httpmq.common.DEFAULT_REQUEST_ID_FIELD)),
            {context.request_id},
        )
        self.assertEqual(response.content, test_msg)

    async def test_sse_get(self):
        """Verify APIClient.get_sse"""

        test_server = self.server

        # Check GET on the ready end-point of httpmq management APIs
        base_url = f"http://{test_server.host}:{test_server.port}"

        uut = httpmq.APIClient(base_url=base_url)

        async def dummy_cb(_):
            """Dummy support callback function"""

        # Case 0: test client side termination
        stop_signal_0 = asyncio.Event()
        rx_caller_0 = asyncio.create_task(
            uut.get_sse(
                path="/msg",
                context=httpmq.RequestContext(),
                stop_loop=stop_signal_0,
                forward_data_cb=dummy_cb,
            )
        )
        await asyncio.sleep(0.3)
        stop_signal_0.set()
        resp = await rx_caller_0
        self.assertEqual(200, resp.status)

        # Case 1: test server side termination
        rx_caller_1 = asyncio.create_task(
            uut.get_sse(
                path="/msg",
                context=httpmq.RequestContext(),
                stop_loop=asyncio.Event(),
                forward_data_cb=dummy_cb,
            )
        )
        await asyncio.sleep(0.1)
        resp = await uut.post(
            path="/msg", context=httpmq.RequestContext().add_param("stop", "1")
        )
        self.assertEqual(200, resp.status)
        resp = await rx_caller_1
        self.assertEqual(200, resp.status)

        # Case 2: test data transfer is correct
        msg_queue = asyncio.Queue()

        async def rx_msg_receive(msg):
            """Support callback function to receive messages"""
            await msg_queue.put(msg)

        stop_signal_2 = asyncio.Event()
        rx_caller_2 = asyncio.create_task(
            uut.get_sse(
                path="/msg",
                context=httpmq.RequestContext(),
                stop_loop=stop_signal_2,
                forward_data_cb=rx_msg_receive,
            )
        )
        for _ in range(2):
            # Send a msg to echo
            msg = str(uuid.uuid4()).encode("utf-8")
            resp = await uut.post(
                path="/msg", context=httpmq.RequestContext(), body=msg
            )
            self.assertEqual(200, resp.status)
            # Wait for the message to come back
            rx_msg = await msg_queue.get()
            msg_queue.task_done()
            self.assertTrue(isinstance(rx_msg, httpmq.APIClient.StreamDataSegment))
            self.assertEqual(
                rx_msg.data.decode("utf-8").strip(), msg.decode("utf-8").strip()
            )
        # Stop the reader
        stop_signal_2.set()
        resp = await rx_caller_2
        self.assertEqual(200, resp.status)
        # Get one last message from queue
        rx_msg = await msg_queue.get()
        msg_queue.task_done()
        self.assertTrue(isinstance(rx_msg, httpmq.APIClient.StreamDataEnd))
