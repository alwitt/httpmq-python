# coding: utf-8

from datetime import date, datetime

from typing import List, Dict, Type

from httpmq.models.base_model_ import Model
from httpmq.models.apis_api_rest_resp_stream_info import ApisAPIRestRespStreamInfo
from httpmq.models.goutils_error_detail import GoutilsErrorDetail
from httpmq import util


class ApisAPIRestRespOneJetStream(Model):
    """NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).

    Do not edit the class manually.
    """

    def __init__(
        self,
        error: GoutilsErrorDetail = None,
        request_id: str = None,
        stream: ApisAPIRestRespStreamInfo = None,
        success: bool = None,
    ):
        """ApisAPIRestRespOneJetStream - a model defined in OpenAPI

        :param error: The error of this ApisAPIRestRespOneJetStream.
        :param request_id: The request_id of this ApisAPIRestRespOneJetStream.
        :param stream: The stream of this ApisAPIRestRespOneJetStream.
        :param success: The success of this ApisAPIRestRespOneJetStream.
        """
        self.openapi_types = {
            "error": GoutilsErrorDetail,
            "request_id": str,
            "stream": ApisAPIRestRespStreamInfo,
            "success": bool,
        }

        self.attribute_map = {
            "error": "error",
            "request_id": "request_id",
            "stream": "stream",
            "success": "success",
        }

        self._error = error
        self._request_id = request_id
        self._stream = stream
        self._success = success

    @classmethod
    def from_dict(cls, dikt: dict) -> "ApisAPIRestRespOneJetStream":
        """Returns the dict as a model

        :param dikt: A dict.
        :return: The apis.APIRestRespOneJetStream of this ApisAPIRestRespOneJetStream.
        """
        return util.deserialize_model(dikt, cls)

    @property
    def error(self):
        """Gets the error of this ApisAPIRestRespOneJetStream.


        :return: The error of this ApisAPIRestRespOneJetStream.
        :rtype: GoutilsErrorDetail
        """
        return self._error

    @error.setter
    def error(self, error):
        """Sets the error of this ApisAPIRestRespOneJetStream.


        :param error: The error of this ApisAPIRestRespOneJetStream.
        :type error: GoutilsErrorDetail
        """

        self._error = error

    @property
    def request_id(self):
        """Gets the request_id of this ApisAPIRestRespOneJetStream.

        RequestID gives the request ID to match against logs

        :return: The request_id of this ApisAPIRestRespOneJetStream.
        :rtype: str
        """
        return self._request_id

    @request_id.setter
    def request_id(self, request_id):
        """Sets the request_id of this ApisAPIRestRespOneJetStream.

        RequestID gives the request ID to match against logs

        :param request_id: The request_id of this ApisAPIRestRespOneJetStream.
        :type request_id: str
        """
        if request_id is None:
            raise ValueError("Invalid value for `request_id`, must not be `None`")

        self._request_id = request_id

    @property
    def stream(self):
        """Gets the stream of this ApisAPIRestRespOneJetStream.


        :return: The stream of this ApisAPIRestRespOneJetStream.
        :rtype: ApisAPIRestRespStreamInfo
        """
        return self._stream

    @stream.setter
    def stream(self, stream):
        """Sets the stream of this ApisAPIRestRespOneJetStream.


        :param stream: The stream of this ApisAPIRestRespOneJetStream.
        :type stream: ApisAPIRestRespStreamInfo
        """

        self._stream = stream

    @property
    def success(self):
        """Gets the success of this ApisAPIRestRespOneJetStream.

        Success indicates whether the request was successful

        :return: The success of this ApisAPIRestRespOneJetStream.
        :rtype: bool
        """
        return self._success

    @success.setter
    def success(self, success):
        """Sets the success of this ApisAPIRestRespOneJetStream.

        Success indicates whether the request was successful

        :param success: The success of this ApisAPIRestRespOneJetStream.
        :type success: bool
        """
        if success is None:
            raise ValueError("Invalid value for `success`, must not be `None`")

        self._success = success
