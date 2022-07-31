"""Wrapper object for operating the httpmq management API"""

from typing import Dict
from httpmq.core import ApiClient
from httpmq.core.api.management_api import ManagementApi
from httpmq.core.models import (
    ManagementJSStreamParam,
    ManagementJSStreamLimits,
    GoutilsRestAPIBaseResponse,
    ApisAPIRestRespAllJetStreams,
    ApisAPIRestRespOneJetStream,
    ApisAPIRestRespStreamInfo,
    ApisAPIRestReqStreamSubjects,
)
from .common import APICallContext, HttpmqAPIError


class MgmtAPIWrapper:
    """Client wrapper object for operating the httpmq management API"""

    def __init__(self, api_client: ApiClient):
        """Constructor

        :param api_client: base client object for interacting with httpmq
        """
        self.client = ManagementApi(api_client=api_client)

    def ready(self, ctxt: APICallContext):
        """Check whether the httpmq management API is ready. Raise exception if not.

        :param ctxt: the caller context
        """
        response: GoutilsRestAPIBaseResponse = self.client.v1_admin_ready_get(
            async_req=False,
            _request_timeout=ctxt.request_timeout_sec,
            _request_auths=ctxt.auth_param,
        )
        # Not ready
        if not response.success:
            raise HttpmqAPIError.new_error(response)

    #####################################################################################
    # Stream related API functions

    def create_stream(self, params: ManagementJSStreamParam, ctxt: APICallContext):
        """Define a new stream

        :param params: the new stream parameters
        :param ctxt: the caller context
        """
        response: GoutilsRestAPIBaseResponse = self.client.v1_admin_stream_post(
            setting=params,
            httpmq_request_id=ctxt.request_id,
            async_req=False,
            _request_timeout=ctxt.request_timeout_sec,
            _request_auths=ctxt.auth_param,
        )
        # Failed
        if not response.success:
            raise HttpmqAPIError.new_error(response)

    def list_all_streams(
        self, ctxt: APICallContext
    ) -> Dict[str, ApisAPIRestRespStreamInfo]:
        """Query for list of all known streams

        :param ctxt: the caller context
        :return: list of known streams
        """
        response: ApisAPIRestRespAllJetStreams = self.client.v1_admin_stream_get(
            httpmq_request_id=ctxt.request_id,
            async_req=False,
            _request_timeout=ctxt.request_timeout_sec,
            _request_auths=ctxt.auth_param,
        )
        # Failed
        if not response.success:
            raise HttpmqAPIError.new_error(response)
        return response.streams

    def get_stream(
        self, stream: str, ctxt: APICallContext
    ) -> ApisAPIRestRespStreamInfo:
        """Query for a particular stream

        :param stream: the stream to query for
        :param ctxt: the caller context
        :return: information on the stream
        """
        response: ApisAPIRestRespOneJetStream = (
            self.client.v1_admin_stream_stream_name_get(
                stream_name=stream,
                httpmq_request_id=ctxt.request_id,
                async_req=False,
                _request_timeout=ctxt.request_timeout_sec,
                _request_auths=ctxt.auth_param,
            )
        )
        # Failed
        if not response.success:
            raise HttpmqAPIError.new_error(response)
        return response.stream

    def change_stream_subjects(
        self, stream: str, new_subjects: list, ctxt: APICallContext
    ):
        """Change the target subjects of a stream

        :param stream: name of the stream
        :param ctxt: the caller context
        """
        response: GoutilsRestAPIBaseResponse = (
            self.client.v1_admin_stream_stream_name_subject_put(
                stream_name=stream,
                subjects=ApisAPIRestReqStreamSubjects(subjects=new_subjects),
                httpmq_request_id=ctxt.request_id,
                async_req=False,
                _request_timeout=ctxt.request_timeout_sec,
                _request_auths=ctxt.auth_param,
            )
        )
        # Failed
        if not response.success:
            raise HttpmqAPIError.new_error(response)

    def update_stream_limits(
        self, stream: str, limits: ManagementJSStreamLimits, ctxt: APICallContext
    ):
        """Update the data retention limits of a stream

        :param stream: name of the stream
        :param limits: new data retention limits
        :param ctxt: the caller context
        """
        response: GoutilsRestAPIBaseResponse = (
            self.client.v1_admin_stream_stream_name_limit_put(
                stream_name=stream,
                limits=limits,
                httpmq_request_id=ctxt.request_id,
                async_req=False,
                _request_timeout=ctxt.request_timeout_sec,
                _request_auths=ctxt.auth_param,
            )
        )
        # Failed
        if not response.success:
            raise HttpmqAPIError.new_error(response)

    def delete_stream(self, stream: str, ctxt: APICallContext):
        """Delete a stream

        :param stream: name of the stream
        :param ctxt: the caller context
        """
        response: GoutilsRestAPIBaseResponse = (
            self.client.v1_admin_stream_stream_name_delete(
                stream_name=stream,
                httpmq_request_id=ctxt.request_id,
                async_req=False,
                _request_timeout=ctxt.request_timeout_sec,
                _request_auths=ctxt.auth_param,
            )
        )
        # Failed
        if not response.success:
            raise HttpmqAPIError.new_error(response)
