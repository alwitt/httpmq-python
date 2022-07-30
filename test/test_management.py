"""Test bench for httpmq.management"""


import unittest
import urllib3
from httpmq import CoreConfiguration, CoreApiClient
from httpmq.common import APICallContext
from httpmq.management import MgmtAPIWrapper
from . import get_unittest_httpmq_mgmt_api_url


class TestManagementPlane(unittest.TestCase):
    """Testbench for httpmq.management"""

    def setUp(self):
        """Prepare for unittest"""
        self.core_cfg = CoreConfiguration(host=get_unittest_httpmq_mgmt_api_url())
        self.core_cfg.debug = True
        self.core_client = CoreApiClient(configuration=self.core_cfg)
        self.mgmt_client = MgmtAPIWrapper(api_client=self.core_client)

    def test_basic_sanity(self):
        """Basic sanity check of management API client"""

        self.mgmt_client.ready(ctxt=APICallContext())

        # Test against an invalid management API URL
        invalid_cfg = CoreConfiguration(host="http://127.0.0.1:17881")
        invalid_cfg.debug = True
        another_client = CoreApiClient(configuration=invalid_cfg)
        another_mgmt_client = MgmtAPIWrapper(api_client=another_client)
        with self.assertRaises(urllib3.exceptions.MaxRetryError):
            another_mgmt_client.ready(ctxt=APICallContext())
