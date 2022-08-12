"""Unit-tests for httpmq python client"""


import asyncio
import logging
import os
from functools import wraps
import unittest
import httpmq


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


def async_test(core_func):
    """
    Decorator to create asyncio context for asyncio methods or functions.
    """

    @wraps(core_func)
    def caller(*args, **kwargs):
        args[0].loop.run_until_complete(core_func(*args, **kwargs))

    return caller


class BaseTestCase(unittest.TestCase):
    """Base class for other unit-tests"""

    @classmethod
    def setUpClass(cls):
        """To be called for all test cases"""
        cls.loop = asyncio.get_event_loop()
        httpmq.configure_sdk_logging(global_log_level=logging.DEBUG)
