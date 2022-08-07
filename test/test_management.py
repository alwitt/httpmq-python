"""Test bench for httpmq.management"""

# pylint: disable=too-many-statements

from datetime import timedelta
import unittest
import uuid
import urllib3
from httpmq import CoreConfiguration, CoreApiClient
import httpmq
from httpmq.common import APICallContext
from httpmq.core.models import (
    ManagementJSStreamParam,
    ManagementJSStreamLimits,
    ManagementJetStreamConsumerParam,
)
from httpmq.management import MgmtAPIWrapper
from . import get_unittest_httpmq_mgmt_api_url


class TestManagementPlane(unittest.TestCase):
    """Test bench for httpmq.management"""

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
        ctxt = APICallContext()
        self.assertEqual(
            self.mgmt_client.create_stream(params=stream_0_param, ctxt=ctxt),
            ctxt.request_id,
        )

        # Case 1: create the same stream again
        ctxt = APICallContext()
        self.assertEqual(
            self.mgmt_client.create_stream(params=stream_0_param, ctxt=ctxt),
            ctxt.request_id,
        )

        # Case 2: create another stream but with same subject
        stream_2_param = ManagementJSStreamParam(
            name=str(uuid.uuid4()), subjects=subjects_0
        )
        with self.assertRaises(httpmq.core.exceptions.ServiceException):
            self.mgmt_client.create_stream(params=stream_2_param, ctxt=APICallContext())

        # Case 3: read back the stream info
        ctxt = APICallContext()
        stream_0_rb, rid = self.mgmt_client.get_stream(stream=stream_0, ctxt=ctxt)
        self.assertEqual(rid, ctxt.request_id)
        self.assertEqual(stream_0_rb.config.name, stream_0)
        self.assertListEqual(stream_0_rb.config.subjects, subjects_0)
        ctxt = APICallContext()
        all_streams, rid = self.mgmt_client.list_all_streams(ctxt=ctxt)
        self.assertEqual(rid, ctxt.request_id)
        self.assertIn(stream_0, all_streams)
        stream_rb = all_streams[stream_0]
        self.assertEqual(stream_rb.config.name, stream_0)
        self.assertListEqual(stream_rb.config.subjects, subjects_0)

        # Case 4: alter subjects for stream
        subjects_4 = [str(uuid.uuid4()), str(uuid.uuid4())]
        ctxt = APICallContext()
        self.assertEqual(
            self.mgmt_client.change_stream_subjects(
                stream=stream_0, new_subjects=subjects_4, ctxt=ctxt
            ),
            ctxt.request_id,
        )
        ctxt = APICallContext()
        stream_0_rb, rid = self.mgmt_client.get_stream(stream=stream_0, ctxt=ctxt)
        self.assertEqual(rid, ctxt.request_id)
        self.assertListEqual(stream_0_rb.config.subjects, subjects_4)

        # Case 5: alter stream data retention
        new_max_age = int(timedelta(hours=1).total_seconds() * 1e9)
        new_limits = ManagementJSStreamLimits(max_age=new_max_age)
        ctxt = APICallContext()
        self.assertEqual(
            self.mgmt_client.update_stream_limits(
                stream=stream_0, limits=new_limits, ctxt=ctxt
            ),
            ctxt.request_id,
        )
        ctxt = APICallContext()
        stream_0_rb, rid = self.mgmt_client.get_stream(stream=stream_0, ctxt=ctxt)
        self.assertEqual(rid, ctxt.request_id)
        self.assertEqual(stream_0_rb.config.max_age, new_max_age)

        # Case 6: delete the stream
        ctxt = APICallContext()
        self.assertEqual(
            self.mgmt_client.delete_stream(stream=stream_0, ctxt=ctxt), ctxt.request_id
        )
        with self.assertRaises(httpmq.core.exceptions.ServiceException):
            self.mgmt_client.get_stream(stream=stream_0, ctxt=APICallContext())

    def test_consumer_management(self):
        """Verify consumer management"""

        self.mgmt_client.ready(ctxt=APICallContext())

        # Case 0: create consumer with unknown stream
        consumer_param = ManagementJetStreamConsumerParam(
            name=str(uuid.uuid4()),
            mode="push",
            max_inflight=2,
            filter_subject=str(uuid.uuid4()),
        )
        with self.assertRaises(httpmq.core.exceptions.ServiceException):
            self.mgmt_client.create_consumer_for_stream(
                stream=str(uuid.uuid4()), params=consumer_param, ctxt=APICallContext()
            )

        # Case 1: create a stream
        stream_1 = str(uuid.uuid4())
        subject_base = str(uuid.uuid4())
        subjects_1 = [f"{subject_base}.a", f"{subject_base}.b"]
        stream_1_param = ManagementJSStreamParam(name=stream_1, subjects=subjects_1)
        ctxt = APICallContext()
        self.assertEqual(
            self.mgmt_client.create_stream(params=stream_1_param, ctxt=ctxt),
            ctxt.request_id,
        )
        ctxt = APICallContext()
        stream_1_rb, rid = self.mgmt_client.get_stream(stream=stream_1, ctxt=ctxt)
        self.assertEqual(rid, ctxt.request_id)
        self.assertEqual(stream_1_rb.config.name, stream_1)
        self.assertListEqual(stream_1_rb.config.subjects, subjects_1)

        # Case 2: create consumer on stream
        consumer_2 = str(uuid.uuid4())
        consumer_param = ManagementJetStreamConsumerParam(
            name=consumer_2,
            mode="push",
            max_inflight=1,
            filter_subject=subjects_1[0],
        )
        ctxt = APICallContext()
        self.assertEqual(
            self.mgmt_client.create_consumer_for_stream(
                stream=stream_1, params=consumer_param, ctxt=ctxt
            ),
            ctxt.request_id,
        )

        # Case 3: create same consumer again on stream
        ctxt = APICallContext()
        self.assertEqual(
            self.mgmt_client.create_consumer_for_stream(
                stream=stream_1, params=consumer_param, ctxt=ctxt
            ),
            ctxt.request_id,
        )

        # Case 4: create same consumer with different subject
        consumer_param = ManagementJetStreamConsumerParam(
            name=consumer_2,
            mode="push",
            max_inflight=1,
            filter_subject=subjects_1[1],
        )
        with self.assertRaises(httpmq.core.exceptions.ServiceException):
            self.mgmt_client.create_consumer_for_stream(
                stream=stream_1, params=consumer_param, ctxt=APICallContext()
            )

        # Case 5: create consumer against unknown subject
        consumer_param = ManagementJetStreamConsumerParam(
            name=str(uuid.uuid4()),
            mode="push",
            max_inflight=1,
            filter_subject=str(uuid.uuid4()),
        )
        with self.assertRaises(httpmq.core.exceptions.ServiceException):
            self.mgmt_client.create_consumer_for_stream(
                stream=stream_1, params=consumer_param, ctxt=APICallContext()
            )

        # Case 6: create consumer against wildcard subject
        consumer_6 = str(uuid.uuid4())
        subject_6 = f"{subject_base}.*"
        consumer_param = ManagementJetStreamConsumerParam(
            name=consumer_6,
            mode="push",
            max_inflight=2,
            filter_subject=subject_6,
        )
        ctxt = APICallContext()
        self.assertEqual(
            self.mgmt_client.create_consumer_for_stream(
                stream=stream_1, params=consumer_param, ctxt=ctxt
            ),
            ctxt.request_id,
        )

        # Case 7: read back consumer info
        ctxt = APICallContext()
        consumer_2_rb, rid = self.mgmt_client.get_consumer_of_stream(
            stream=stream_1, consumer=consumer_2, ctxt=ctxt
        )
        self.assertEqual(rid, ctxt.request_id)
        self.assertEqual(consumer_2_rb.config.max_ack_pending, 1)
        self.assertEqual(consumer_2_rb.config.filter_subject, subjects_1[0])
        ctxt = APICallContext()
        all_consumers, rid = self.mgmt_client.list_all_consumer_of_stream(
            stream=stream_1, ctxt=ctxt
        )
        self.assertEqual(rid, ctxt.request_id)
        self.assertEqual(len(all_consumers), 2)
        self.assertIn(consumer_6, all_consumers)
        consumer_6_rb = all_consumers[consumer_6]
        self.assertEqual(consumer_6_rb.config.max_ack_pending, 2)
        self.assertEqual(consumer_6_rb.config.filter_subject, subject_6)

        # Case 8: delete the consumer
        ctxt = APICallContext()
        self.assertEqual(
            self.mgmt_client.delete_consumer_on_stream(
                stream=stream_1, consumer=consumer_2, ctxt=ctxt
            ),
            ctxt.request_id,
        )
        ctxt = APICallContext()
        self.assertEqual(
            self.mgmt_client.delete_consumer_on_stream(
                stream=stream_1, consumer=consumer_6, ctxt=ctxt
            ),
            ctxt.request_id,
        )
        ctxt = APICallContext()
        all_consumers, rid = self.mgmt_client.list_all_consumer_of_stream(
            stream=stream_1, ctxt=ctxt
        )
        self.assertEqual(rid, ctxt.request_id)
        self.assertEqual(len(all_consumers), 0)

        # Delete the stream
        ctxt = APICallContext()
        self.assertEqual(
            self.mgmt_client.delete_stream(stream=stream_1, ctxt=ctxt), ctxt.request_id
        )
        with self.assertRaises(httpmq.core.exceptions.ServiceException):
            self.mgmt_client.get_stream(stream=stream_1, ctxt=APICallContext())
