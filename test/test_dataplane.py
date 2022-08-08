"""Test bench for httpmq.dataplane"""


import unittest
import uuid
import urllib3
from httpmq import CoreConfiguration, CoreApiClient
import httpmq
from httpmq.common import APICallContext
from httpmq.core.models import (
    ManagementJSStreamParam,
    ManagementJetStreamConsumerParam,
)
from httpmq.dataplane import DataAPIWrapper, RxMessageSplitter
from httpmq.management import MgmtAPIWrapper
from . import get_unittest_httpmq_data_api_url, get_unittest_httpmq_mgmt_api_url


class TestDataPlane(unittest.TestCase):
    """Test bench for httpmq.dataplane"""

    def setUp(self):
        """Prepare for unittest"""
        self.core_mgmt_cfg = CoreConfiguration(host=get_unittest_httpmq_mgmt_api_url())
        self.core_mgmt_cfg.debug = True
        self.core_mgmt_client = CoreApiClient(configuration=self.core_mgmt_cfg)
        self.mgmt_client = MgmtAPIWrapper(api_client=self.core_mgmt_client)
        self.core_data_cfg = CoreConfiguration(host=get_unittest_httpmq_data_api_url())
        self.core_data_cfg.debug = True
        self.core_data_client = CoreApiClient(configuration=self.core_data_cfg)
        self.data_client = DataAPIWrapper(api_client=self.core_data_client)

    def test_message_splitter(self):
        """Basic sanity check RxMessageSplitter"""

        uut = RxMessageSplitter()

        test_cases = [
            {
                "input": b'{"hello":',
                "expect": [],
            },
            {
                "input": b'"world"}\n{"a":12,"c',
                "expect": [{"hello": "world"}],
            },
            {
                "input": b'":{"b":1.31,"d":"hhase"}}\n{"hello":"wow"}',
                "expect": [{"a": 12, "c": {"b": 1.31, "d": "hhase"}}, {"hello": "wow"}],
            },
            {
                "input": b'{"a":"a8931",',
                "expect": [],
            },
            {
                "input": None,
                "expect": [],
            },
            {
                "input": "",
                "expect": [],
            },
            {
                "input": b'"b":-0.0193}',
                "expect": [{"a": "a8931", "b": -0.0193}],
            },
        ]
        for one_case in test_cases:
            parsed_list = uut.process_new_segment(one_case["input"])
            self.assertListEqual(one_case["expect"], parsed_list)

    def test_basic_sanity(self):
        """Basic sanity check of dataplane API client"""

        self.data_client.ready(ctxt=APICallContext())

        # Test against an invalid management API URL
        invalid_cfg = CoreConfiguration(host="http://127.0.0.1:17881")
        invalid_cfg.debug = True
        another_client = CoreApiClient(configuration=invalid_cfg)
        another_mgmt_client = DataAPIWrapper(api_client=another_client)
        with self.assertRaises(urllib3.exceptions.MaxRetryError):
            another_mgmt_client.ready(ctxt=APICallContext())

    def test_push_subscribe(self):
        """Basic functionality test of push subscription"""

        self.mgmt_client.ready(ctxt=APICallContext())
        self.data_client.ready(ctxt=APICallContext())

        # Case 0: create a stream and consumer
        stream_0 = str(uuid.uuid4())
        subject_base = str(uuid.uuid4())
        subjects_0 = [f"{subject_base}.a", f"{subject_base}.b"]
        subject_wildcard = f"{subject_base}.*"
        stream_0_param = ManagementJSStreamParam(name=stream_0, subjects=subjects_0)
        ctxt = APICallContext()
        self.assertEqual(
            self.mgmt_client.create_stream(params=stream_0_param, ctxt=ctxt),
            ctxt.request_id,
        )
        ctxt = APICallContext()
        stream_0_rb, rid = self.mgmt_client.get_stream(stream=stream_0, ctxt=ctxt)
        self.assertEqual(rid, ctxt.request_id)
        self.assertEqual(stream_0_rb.config.name, stream_0)
        self.assertListEqual(stream_0_rb.config.subjects, subjects_0)
        consumer_0 = str(uuid.uuid4())
        consumer_param = ManagementJetStreamConsumerParam(
            name=consumer_0,
            mode="push",
            max_inflight=1,
            filter_subject=subjects_0[0],
        )
        ctxt = APICallContext()
        self.assertEqual(
            self.mgmt_client.create_consumer_for_stream(
                stream=stream_0, params=consumer_param, ctxt=ctxt
            ),
            ctxt.request_id,
        )
        consumer_1 = str(uuid.uuid4())
        consumer_param = ManagementJetStreamConsumerParam(
            name=consumer_1,
            mode="push",
            max_inflight=1,
            filter_subject=subjects_0[1],
        )
        ctxt = APICallContext()
        self.assertEqual(
            self.mgmt_client.create_consumer_for_stream(
                stream=stream_0, params=consumer_param, ctxt=ctxt
            ),
            ctxt.request_id,
        )
        consumer_2 = str(uuid.uuid4())
        consumer_param = ManagementJetStreamConsumerParam(
            name=consumer_2,
            mode="push",
            max_inflight=1,
            filter_subject=subject_wildcard,
        )
        ctxt = APICallContext()
        self.assertEqual(
            self.mgmt_client.create_consumer_for_stream(
                stream=stream_0, params=consumer_param, ctxt=ctxt
            ),
            ctxt.request_id,
        )

        # There is no clean way to shutdown these threads

        # # Case 1: subscribe for messages
        # c0_rx0_msg_queue = queue.Queue()
        # c1_rx0_msg_queue = queue.Queue()
        # c2_rx0_msg_queue = queue.Queue()

        # def write_to_c0_rx0_msg_queue(msg: ReceivedMessage):
        #     c0_rx0_msg_queue.put(msg)

        # def write_to_c1_rx0_msg_queue(msg: ReceivedMessage):
        #     c1_rx0_msg_queue.put(msg)

        # def write_to_c2_rx0_msg_queue(msg: ReceivedMessage):
        #     c2_rx0_msg_queue.put(msg)

        # # Helper thread to run the RX loop
        # def read_rx_msg(
        #     consumer: str, subject_filter: str, rx_msg_log_cb, ctxt: APICallContext
        # ):
        #     with self.assertRaises(Exception):
        #         self.data_client.push_subscribe(
        #             stream=stream_0,
        #             consumer=consumer,
        #             subject_filter=subject_filter,
        #             process_rx_msg_cb=rx_msg_log_cb,
        #             ctxt=ctxt,
        #         )

        # rx0_ctxt = APICallContext()
        # rx1_ctxt = APICallContext()
        # rx2_ctxt = APICallContext()
        # threading.Thread(
        #     target=read_rx_msg,
        #     args=(consumer_0, subjects_0[0], write_to_c0_rx0_msg_queue, rx0_ctxt),
        # ).start()
        # threading.Thread(
        #     target=read_rx_msg,
        #     args=(consumer_1, subjects_0[1], write_to_c1_rx0_msg_queue, rx1_ctxt),
        # ).start()
        # threading.Thread(
        #     target=read_rx_msg,
        #     args=(consumer_2, subject_wildcard, write_to_c2_rx0_msg_queue, rx2_ctxt),
        # ).start()

        # Delete the stream
        ctxt = APICallContext()
        self.assertEqual(
            self.mgmt_client.delete_stream(stream=stream_0, ctxt=ctxt), ctxt.request_id
        )
        with self.assertRaises(httpmq.core.exceptions.ServiceException):
            self.mgmt_client.get_stream(stream=stream_0, ctxt=APICallContext())
