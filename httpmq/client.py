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
        """Abstract object representing a response to a request"""

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
        msgs.append(
            "[%s] > %s %s HTTP/%d.%d"
            % (
                trace_config_ctx.trace_request_ctx.request_id,
                params.method,
                params.url.path,
                session.version[0],
                session.version[1],
            )
        )
        msgs.append(
            "[%s] > Host: %s"
            % (
                trace_config_ctx.trace_request_ctx.request_id,
                params.url.host,
            )
        )
        # Log the headers
        for header_name, header_value in params.headers.items():
            msgs.append(
                "[%s] > %s: %s"
                % (
                    trace_config_ctx.trace_request_ctx.request_id,
                    header_name,
                    header_value,
                )
            )
        for msg in msgs:
            LOG.debug(msg)

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
        msgs.append(
            "[%s] < HTTP/%d.%d %d %s"
            % (
                trace_config_ctx.trace_request_ctx.request_id,
                session.version[0],
                session.version[1],
                params.response.status,
                params.response.reason,
            )
        )
        # Log the headers
        for header_name, header_value in params.response.headers.items():
            msgs.append(
                "[%s] < %s: %s"
                % (
                    trace_config_ctx.trace_request_ctx.request_id,
                    header_name,
                    header_value,
                )
            )
        # Log the duration
        msgs.append(
            "[%s] Request Duration == %0.3f ms"
            % (trace_config_ctx.trace_request_ctx.request_id, duration * 1000)
        )
        for msg in msgs:
            LOG.debug(msg)

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
        msgs.append(
            "[%s] Request Duration == %0.3f ms"
            % (trace_config_ctx.trace_request_ctx.request_id, duration * 1000)
        )
        for msg in msgs:
            LOG.debug(msg)

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

    async def get(self, path: str, ctxt: RequestContext) -> Response:
        """HTTP GET wrapper

        :param path: GET target path
        :param ctxt: request context
        :param params: URL parameters
        :return: response
        """
        # Define the complete header map
        final_headers = CIMultiDict()
        if self.base_headers is not None:
            final_headers.extend(CIMultiDictProxy(self.base_headers))
        final_headers.extend(ctxt.get_headers())
        # Make the request
        async with self.session.get(
            url=path,
            params=ctxt.additional_params,
            headers=final_headers,
            timeout=(
                ctxt.request_timeout
                if ctxt.request_timeout is not None
                else self.base_timeout
            ),
            trace_request_ctx=ctxt,
        ) as resp:
            # Convert the response object to a wrapper object
            return APIClient.Response(resp, await resp.read())
