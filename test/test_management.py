"""Test bench for httpmq.management"""


from datetime import timedelta
import unittest
import uuid
import urllib3
from httpmq import CoreConfiguration, CoreApiClient
import httpmq
from httpmq.common import APICallContext
from httpmq.core.models import ManagementJSStreamParam, ManagementJSStreamLimits
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

    def test_stream_management(self):
        """Verify stream management"""

        self.mgmt_client.ready(ctxt=APICallContext())

        # Case 0: create a stream
        stream_0 = str(uuid.uuid4())
        subjects_0 = [str(uuid.uuid4())]
        stream_0_param = ManagementJSStreamParam(name=stream_0, subjects=subjects_0)
        self.mgmt_client.create_stream(params=stream_0_param, ctxt=APICallContext())

        # Case 1: create the same stream again
        self.mgmt_client.create_stream(params=stream_0_param, ctxt=APICallContext())

        # Case 2: create another stream but with same subject
        stream_2_param = ManagementJSStreamParam(
            name=str(uuid.uuid4()), subjects=subjects_0
        )
        with self.assertRaises(httpmq.core.exceptions.ServiceException):
            self.mgmt_client.create_stream(params=stream_2_param, ctxt=APICallContext())

        # Case 3: read back the stream info
        stream_0_rb = self.mgmt_client.get_stream(
            stream=stream_0, ctxt=APICallContext()
        )
        self.assertEqual(stream_0_rb.config.name, stream_0)
        self.assertListEqual(stream_0_rb.config.subjects, subjects_0)
        all_streams = self.mgmt_client.list_all_streams(ctxt=APICallContext())
        self.assertIn(stream_0, all_streams)
        stream_rb = all_streams[stream_0]
        self.assertEqual(stream_rb.config.name, stream_0)
        self.assertListEqual(stream_rb.config.subjects, subjects_0)

        # Case 4: alter subjects for stream
        subjects_4 = [str(uuid.uuid4()), str(uuid.uuid4())]
        self.mgmt_client.change_stream_subjects(
            stream=stream_0, new_subjects=subjects_4, ctxt=APICallContext()
        )
        stream_0_rb = self.mgmt_client.get_stream(
            stream=stream_0, ctxt=APICallContext()
        )
        self.assertListEqual(stream_0_rb.config.subjects, subjects_4)

        # Case 5: alter stream data retention
        new_max_age = int(timedelta(hours=1).total_seconds() * 1e9)
        new_limits = ManagementJSStreamLimits(max_age=new_max_age)
        self.mgmt_client.update_stream_limits(
            stream=stream_0, limits=new_limits, ctxt=APICallContext()
        )
        stream_0_rb = self.mgmt_client.get_stream(
            stream=stream_0, ctxt=APICallContext()
        )
        self.assertEqual(stream_0_rb.config.max_age, new_max_age)

        # Case 6: delete the stream
        self.mgmt_client.delete_stream(stream=stream_0, ctxt=APICallContext())
        with self.assertRaises(httpmq.core.exceptions.ServiceException):
            self.mgmt_client.get_stream(stream=stream_0, ctxt=APICallContext())
