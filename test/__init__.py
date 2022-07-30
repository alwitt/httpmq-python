"""Unit-tests for httpmq python client"""


import os


def get_unittest_httpmq_mgmt_api_url() -> str:
    """Fetch the httpmq management API URL for testing

    :return: the httpmq managment API URL
    """
    return os.getenv("HTTPMQ_MGMT_API_URL", "http://127.0.0.1:4100")


def get_unittest_httpmq_data_api_url() -> str:
    """Fetch the httpmq dataplane API URL for testing

    :return: the httpmq dataplane API URL
    """
    return os.getenv("HTTPMQ_DATA_API_URL", "http://127.0.0.1:4101")
