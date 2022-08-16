"""aiohttp Transport client for connecting to httpmq"""

# pylint: disable=too-few-public-methods
# pylint: disable=too-many-arguments
# pylint: disable=consider-using-f-string

import asyncio
import logging
import ssl
import traceback
from types import SimpleNamespace
from typing import Optional
import aiohttp
from multidict import CIMultiDict, CIMultiDictProxy

from httpmq.common import RequestContext

LOG = logging.getLogger("httpmq-sdk.client")


class APIClient:
    """Handles communication with httpmq"""

    class Response:
        """Object representing a response to a request"""

        def __init__(
            self,
            original_resp: aiohttp.ClientResponse,
            resp_content: Optional[bytes] = None,
        ):
            """Constructor

            :param original_resp: the original response from aiohttp
            :param resp_content: response content
            """
            self.host = original_resp.host
            self.url = original_resp.real_url
            self.status = original_resp.status
            self.method = original_resp.method
            self.headers = original_resp.headers
            self.content_type = original_resp.content_type
            self.content = resp_content

    class StreamDataSegment:
        """Object containing a data segment from a stream"""

        def __init__(self, data: bytes):
            """Constructor

            :param data: data segment
            """
            self.data = data

    class StreamDataEnd:
        """Object indicating the end of a data stream"""

        def __init__(self):
            """Constructor"""

    @staticmethod
    async def on_request_start(
        session: aiohttp.ClientSession,
        trace_config_ctx: SimpleNamespace,
        params: aiohttp.TraceRequestStartParams,
    ):
        """Called on start of a request

        :param session: the aiohttp session
        :param trace_config_ctx: request config
        :param params: request params
        """
        trace_config_ctx.start_time = asyncio.get_event_loop().time()
        msgs = []
        msgs.append(f"[{trace_config_ctx.trace_request_ctx.request_id}] Request ==>")
        msgs.append(
            f"> {params.method} {params.url.path} HTTP/{session.version[0]}.{session.version[1]}"
        )
        msgs.append(f"> Host: {params.url.host}")
        # Log the headers
        for header_name, header_value in params.headers.items():
            msgs.append(f"> {header_name}: {header_value}")
        LOG.debug("\n".join(msgs))

    @staticmethod
    async def on_request_end(
        session: aiohttp.ClientSession,
        trace_config_ctx: SimpleNamespace,
        params: aiohttp.TraceRequestEndParams,
    ):
        """Called at end of a request

        :param session: the aiohttp session
        :param trace_config_ctx: request config
        :param params: request params
        """
        end_time = asyncio.get_event_loop().time()
        duration = end_time - trace_config_ctx.start_time
        msgs = []
        msgs.append(f"[{trace_config_ctx.trace_request_ctx.request_id}] Response <==")
        msgs.append(
            "< HTTP/%d.%d %d %s"
            % (
                session.version[0],
                session.version[1],
                params.response.status,
                params.response.reason,
            )
        )
        # Log the headers
        for header_name, header_value in params.response.headers.items():
            msgs.append(f"< {header_name}: {header_value}")
        # Log the duration
        msgs.append(f"Request Duration == {duration*1e3:.3} ms")
        LOG.debug("\n".join(msgs))

    @staticmethod
    async def on_request_exception(
        session: aiohttp.ClientSession,
        trace_config_ctx: SimpleNamespace,
        params: aiohttp.TraceRequestExceptionParams,
    ):
        """Called if request ends with an exception

        :param session: the aiohttp session
        :param trace_config_ctx: request config
        :param params: request params
        """
        end_time = asyncio.get_event_loop().time()
        duration = end_time - trace_config_ctx.start_time
        msgs = []
        msgs.append(
            "[%s] > %s %s HTTP/%d.%d raised\n%s"
            % (
                trace_config_ctx.trace_request_ctx.request_id,
                params.method,
                params.url.path,
                session.version[0],
                session.version[1],
                "".join(
                    traceback.format_exception(
                        type(params.exception),
                        params.exception,
                        params.exception.__traceback__,
                    )
                ),
            )
        )
        # Log the duration
        msgs.append(f"Request Duration == {duration*1e3:.3} ms")
        LOG.debug("\n".join(msgs))

    def __init__(
        self,
        base_url: str,
        common_headers: Optional[CIMultiDict] = None,
        http_timeout: Optional[aiohttp.ClientTimeout] = None,
        trace_config: Optional[aiohttp.TraceConfig] = None,
        ssl_context: Optional[ssl.SSLContext] = None,
    ):
        """Constructor

        :param base_url: the base URL of the target
        :param common_headers: common headers to apply to all requests
        :param http_timeout: common request timeout settings
        :param trace_config: request trace setting
        :param ssl_context: common request SSL context
        """
        # Define request tracking hooks
        traces = []
        if trace_config is not None:
            traces.append(trace_config)
        access_log = aiohttp.TraceConfig()
        access_log.on_request_start.append(APIClient.on_request_start)
        access_log.on_request_end.append(APIClient.on_request_end)
        access_log.on_request_exception.append(APIClient.on_request_exception)
        traces.append(access_log)

        # Create new session
        self.session = aiohttp.ClientSession(base_url=base_url, trace_configs=traces)

        self.ssl = ssl_context
        self.base_headers = common_headers
        self.base_timeout = (
            http_timeout
            if http_timeout is not None
            else aiohttp.ClientTimeout(total=60)
        )
        LOG.debug("Defined aiohttp client connecting to '%s'", base_url)

    async def get(self, path: str, context: RequestContext) -> Response:
        """HTTP GET wrapper

        :param path: GET target path
        :param context: request context
        :return: response
        """
        # Define the complete header map
        final_headers = CIMultiDict()
        if self.base_headers is not None:
            final_headers.extend(CIMultiDictProxy(self.base_headers))
        final_headers.extend(context.get_headers())
        # Make the request
        async with self.session.get(
            url=path,
            params=context.additional_params,
            headers=final_headers,
            timeout=(
                context.request_timeout
                if context.request_timeout is not None
                else self.base_timeout
            ),
            trace_request_ctx=context,
        ) as resp:
            # Convert the response object to a wrapper object
            return APIClient.Response(resp, await resp.read())

    async def get_sse(
        self,
        path: str,
        context: RequestContext,
        stop_loop: asyncio.Event,
        forward_data_cb,
        loop_interval_sec: float = 0.25,
    ) -> Response:
        """HTTP GET wrapper supporting server-send-event endpoints

        The client will continue to read data from the server until
          * The caller request the loop to stop
          * Some error occurs
          * The server closes the connection

        The receives bytes is passed back via a call-back function.

        The loop uses non-blocking read function, so it sleeps between reads.

        :param path: GET target path
        :param context: request context
        :param stop_loop: signal to indicate the loop should stop
        :param forward_data_cb: callback function used to forward data back to the caller
        :param loop_interval_sec: the sleep interval between non-blocking reads
        :return: response
        """
        # Define the complete header map
        final_headers = CIMultiDict()
        if self.base_headers is not None:
            final_headers.extend(CIMultiDictProxy(self.base_headers))
        final_headers.extend(context.get_headers())
        # Make the request
        async with self.session.get(
            url=path,
            params=context.additional_params,
            headers=final_headers,
            timeout=(
                context.request_timeout
                if context.request_timeout is not None
                else self.base_timeout
            ),
            trace_request_ctx=context,
        ) as resp:
            # Start reading the event stream
            while not stop_loop.is_set() and not resp.content.at_eof():
                data_segment = resp.content.read_nowait()
                if data_segment:
                    await forward_data_cb(
                        APIClient.StreamDataSegment(data=data_segment)
                    )
                else:
                    # Nothing, try again later
                    await asyncio.sleep(loop_interval_sec)
            # Indicate end-of-stream
            await forward_data_cb(APIClient.StreamDataEnd())
            # Convert the response object to a wrapper object
            return APIClient.Response(resp, None)

    async def post(
        self, path: str, context: RequestContext, body: bytes = None
    ) -> Response:
        """HTTP POST wrapper

        :param path: POST target path
        :param context: request context
        :param body: POST body
        :return: response
        """
        # Define the complete header map
        final_headers = CIMultiDict()
        if self.base_headers is not None:
            final_headers.extend(CIMultiDictProxy(self.base_headers))
        final_headers.extend(context.get_headers())
        # Make the request
        async with self.session.post(
            url=path,
            params=context.additional_params,
            headers=final_headers,
            timeout=(
                context.request_timeout
                if context.request_timeout is not None
                else self.base_timeout
            ),
            trace_request_ctx=context,
            data=body,
        ) as resp:
            # Convert the response object to a wrapper object
            return APIClient.Response(resp, await resp.read())

    async def put(
        self, path: str, context: RequestContext, body: bytes = None
    ) -> Response:
        """HTTP PUT wrapper

        :param path: PUT target path
        :param context: request context
        :param body: PUT body
        :return: response
        """
        # Define the complete header map
        final_headers = CIMultiDict()
        if self.base_headers is not None:
            final_headers.extend(CIMultiDictProxy(self.base_headers))
        final_headers.extend(context.get_headers())
        # Make the request
        async with self.session.put(
            url=path,
            params=context.additional_params,
            headers=final_headers,
            timeout=(
                context.request_timeout
                if context.request_timeout is not None
                else self.base_timeout
            ),
            trace_request_ctx=context,
            data=body,
        ) as resp:
            # Convert the response object to a wrapper object
            return APIClient.Response(resp, await resp.read())

    async def delete(self, path: str, context: RequestContext) -> Response:
        """HTTP DELETE wrapper

        :param path: DELETE target path
        :param context: request context
        :return: response
        """
        # Define the complete header map
        final_headers = CIMultiDict()
        if self.base_headers is not None:
            final_headers.extend(CIMultiDictProxy(self.base_headers))
        final_headers.extend(context.get_headers())
        # Make the request
        async with self.session.delete(
            url=path,
            params=context.additional_params,
            headers=final_headers,
            timeout=(
                context.request_timeout
                if context.request_timeout is not None
                else self.base_timeout
            ),
            trace_request_ctx=context,
        ) as resp:
            # Convert the response object to a wrapper object
            return APIClient.Response(resp, await resp.read())
