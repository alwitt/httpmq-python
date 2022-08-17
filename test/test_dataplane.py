"""Test bench for httpmq.dataplane"""

# pylint: disable=too-many-locals
# pylint: disable=too-many-statements

import asyncio
from typing import Union
import uuid
import aiohttp
from httpmq.client import APIClient
from httpmq.common import HttpmqAPIError, RequestContext
from httpmq.dataplane import DataAPIWrapper, ReceivedMessage
from httpmq.management import MgmtAPIWrapper
from httpmq.models import (
    ManagementJSStreamParam,
    ManagementJetStreamConsumerParam,
)
from . import (
    BaseTestCase,
    async_test,
    get_unittest_httpmq_data_api_url,
    get_unittest_httpmq_mgmt_api_url,
)


class TestDataplane(BaseTestCase):
    """Test bench for httpmq.dataplane"""

    def test_message_splitter(self):
        """Basic sanity check RxMessageSplitter"""

        uut = DataAPIWrapper.RxMessageSplitter()

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

    @async_test
    async def test_basic_sanity(self):
        """Basic sanity check of management API client"""

        core_client = APIClient(base_url=get_unittest_httpmq_data_api_url())
        data_client = DataAPIWrapper(api_client=core_client)
        await data_client.ready(context=RequestContext())

        another_client = APIClient(base_url="http://127.0.0.1:17881")
        another_data_client = DataAPIWrapper(api_client=another_client)
        with self.assertRaises(aiohttp.client_exceptions.ClientConnectorError):
            await another_data_client.ready(context=RequestContext())

    @async_test
    async def test_push_subscribe(self):
        """Basic functionality test of push subscription"""

        mgmt_client = MgmtAPIWrapper(
            api_client=APIClient(base_url=get_unittest_httpmq_mgmt_api_url())
        )
        await mgmt_client.ready(context=RequestContext())

        data_client = DataAPIWrapper(
            api_client=APIClient(base_url=get_unittest_httpmq_data_api_url())
        )
        await data_client.ready(context=RequestContext())

        # Case 0: create a stream and consumer
        stream_0 = str(uuid.uuid4())
        subject_base = str(uuid.uuid4())
        subjects_0 = [f"{subject_base}.a", f"{subject_base}.b"]
        subject_wildcard = f"{subject_base}.*"
        stream_0_param = ManagementJSStreamParam(name=stream_0, subjects=subjects_0)
        context = RequestContext()
        self.assertEqual(
            context.request_id,
            await mgmt_client.create_stream(params=stream_0_param, context=context),
        )
        context = RequestContext()
        stream_0_rb, rid = await mgmt_client.get_stream(
            stream=stream_0, context=context
        )
        self.assertEqual(rid, context.request_id)
        self.assertEqual(stream_0_rb.config.name, stream_0)
        self.assertListEqual(stream_0_rb.config.subjects, subjects_0)
        consumer_0 = str(uuid.uuid4())
        consumer_param = ManagementJetStreamConsumerParam(
            name=consumer_0,
            mode="push",
            max_inflight=1,
            filter_subject=subjects_0[0],
        )
        context = RequestContext()
        self.assertEqual(
            context.request_id,
            await mgmt_client.create_consumer_for_stream(
                stream=stream_0, params=consumer_param, context=context
            ),
        )
        consumer_1 = str(uuid.uuid4())
        consumer_param = ManagementJetStreamConsumerParam(
            name=consumer_1,
            mode="push",
            max_inflight=1,
            filter_subject=subjects_0[1],
        )
        context = RequestContext()
        self.assertEqual(
            context.request_id,
            await mgmt_client.create_consumer_for_stream(
                stream=stream_0, params=consumer_param, context=context
            ),
        )
        consumer_2 = str(uuid.uuid4())
        consumer_param = ManagementJetStreamConsumerParam(
            name=consumer_2,
            mode="push",
            max_inflight=1,
            filter_subject=subject_wildcard,
        )
        context = RequestContext()
        self.assertEqual(
            context.request_id,
            await mgmt_client.create_consumer_for_stream(
                stream=stream_0, params=consumer_param, context=context
            ),
        )
        # Verify the consumers are defined
        context = RequestContext()
        all_consumers, rid = await mgmt_client.list_all_consumer_of_stream(
            stream=stream_0, context=context
        )
        self.assertEqual(rid, context.request_id)
        self.assertIn(consumer_0, all_consumers)
        consumer_rb = all_consumers[consumer_0]
        self.assertEqual(consumer_rb.config.filter_subject, subjects_0[0])
        self.assertIn(consumer_1, all_consumers)
        consumer_rb = all_consumers[consumer_1]
        self.assertEqual(consumer_rb.config.filter_subject, subjects_0[1])
        self.assertIn(consumer_2, all_consumers)
        consumer_rb = all_consumers[consumer_2]
        self.assertEqual(consumer_rb.config.filter_subject, subject_wildcard)

        async def dummy_rx_handler(_: Union[ReceivedMessage, HttpmqAPIError]):
            """Dummy RX receive function"""

        # Case 1: test client disconnect
        rx_runner_stop_signal = asyncio.Event()
        rx_runner = asyncio.create_task(
            data_client.push_subscribe(
                stream=stream_0,
                consumer=consumer_0,
                subject_filter=subjects_0[0],
                context=RequestContext(),
                stop_loop=rx_runner_stop_signal,
                forward_data_cb=dummy_rx_handler,
            )
        )
        await asyncio.sleep(0.1)
        rx_runner_stop_signal.set()
        await rx_runner

        #############################################################################
        # Start the three consumer receive loops

        consumer_0_rx_msgs = asyncio.Queue()
        consumer_1_rx_msgs = asyncio.Queue()
        consumer_2_rx_msgs = asyncio.Queue()

        async def consumer_0_store_msg(msg: Union[ReceivedMessage, HttpmqAPIError]):
            """Consumer 0 record message"""
            self.assertIsInstance(msg, ReceivedMessage)
            await consumer_0_rx_msgs.put(msg)

        async def consumer_1_store_msg(msg: Union[ReceivedMessage, HttpmqAPIError]):
            """Consumer 1 record message"""
            self.assertIsInstance(msg, ReceivedMessage)
            await consumer_1_rx_msgs.put(msg)

        async def consumer_2_store_msg(msg: Union[ReceivedMessage, HttpmqAPIError]):
            """Consumer 2 record message"""
            self.assertIsInstance(msg, ReceivedMessage)
            await consumer_2_rx_msgs.put(msg)

        consumer_0_stop = asyncio.Event()
        consumer_0_runner_context = RequestContext()
        consumer_0_rx_runner = asyncio.create_task(
            data_client.push_subscribe(
                stream=stream_0,
                consumer=consumer_0,
                subject_filter=subjects_0[0],
                context=consumer_0_runner_context,
                stop_loop=consumer_0_stop,
                forward_data_cb=consumer_0_store_msg,
            )
        )

        consumer_1_stop = asyncio.Event()
        consumer_1_runner_context = RequestContext()
        consumer_1_rx_runner = asyncio.create_task(
            data_client.push_subscribe(
                stream=stream_0,
                consumer=consumer_1,
                subject_filter=subjects_0[1],
                context=consumer_1_runner_context,
                stop_loop=consumer_1_stop,
                forward_data_cb=consumer_1_store_msg,
            )
        )

        consumer_2_stop = asyncio.Event()
        consumer_2_runner_context = RequestContext()
        consumer_2_rx_runner = asyncio.create_task(
            data_client.push_subscribe(
                stream=stream_0,
                consumer=consumer_2,
                subject_filter=subject_wildcard,
                context=consumer_2_runner_context,
                stop_loop=consumer_2_stop,
                forward_data_cb=consumer_2_store_msg,
            )
        )

        # Case 2: Send message to subject.0
        msg = str(uuid.uuid4()).encode("utf-8")
        context = RequestContext()
        self.assertEqual(
            context.request_id,
            await data_client.publish(
                subject=subjects_0[0], message=msg, context=context
            ),
        )
        # Verify consumer 0 received it
        received = await consumer_0_rx_msgs.get()
        consumer_0_rx_msgs.task_done()
        self.assertIsInstance(received, ReceivedMessage)
        rx_msg: ReceivedMessage = received
        self.assertEqual(rx_msg.stream, stream_0)
        self.assertEqual(rx_msg.consumer, consumer_0)
        self.assertEqual(rx_msg.subject, subjects_0[0])
        self.assertEqual(rx_msg.message, msg)
        context = RequestContext()
        self.assertEqual(
            context.request_id,
            await data_client.send_ack_simple(original_msg=rx_msg, context=context),
        )
        # Verify consumer 2 received it
        received = await consumer_2_rx_msgs.get()
        consumer_2_rx_msgs.task_done()
        self.assertIsInstance(received, ReceivedMessage)
        rx_msg: ReceivedMessage = received
        self.assertEqual(rx_msg.stream, stream_0)
        self.assertEqual(rx_msg.consumer, consumer_2)
        self.assertEqual(rx_msg.subject, subject_wildcard)
        self.assertEqual(rx_msg.message, msg)
        context = RequestContext()
        self.assertEqual(
            context.request_id,
            await data_client.send_ack_simple(original_msg=rx_msg, context=context),
        )
        # Verify consumer 1 did not receive anything
        with self.assertRaises(asyncio.QueueEmpty):
            consumer_1_rx_msgs.get_nowait()

        # Case 3: Send message to subject.1
        msg = str(uuid.uuid4()).encode("utf-8")
        context = RequestContext()
        self.assertEqual(
            context.request_id,
            await data_client.publish(
                subject=subjects_0[1], message=msg, context=context
            ),
        )
        # Verify consumer 1 received it
        received = await consumer_1_rx_msgs.get()
        consumer_1_rx_msgs.task_done()
        self.assertIsInstance(received, ReceivedMessage)
        rx_msg: ReceivedMessage = received
        self.assertEqual(rx_msg.stream, stream_0)
        self.assertEqual(rx_msg.consumer, consumer_1)
        self.assertEqual(rx_msg.subject, subjects_0[1])
        self.assertEqual(rx_msg.message, msg)
        context = RequestContext()
        self.assertEqual(
            context.request_id,
            await data_client.send_ack_simple(original_msg=rx_msg, context=context),
        )
        # Verify consumer 2 received it
        received = await consumer_2_rx_msgs.get()
        consumer_2_rx_msgs.task_done()
        self.assertIsInstance(received, ReceivedMessage)
        rx_msg: ReceivedMessage = received
        self.assertEqual(rx_msg.stream, stream_0)
        self.assertEqual(rx_msg.consumer, consumer_2)
        self.assertEqual(rx_msg.subject, subject_wildcard)
        self.assertEqual(rx_msg.message, msg)
        context = RequestContext()
        self.assertEqual(
            context.request_id,
            await data_client.send_ack_simple(original_msg=rx_msg, context=context),
        )
        # Verify consumer 0 did not receive anything
        with self.assertRaises(asyncio.QueueEmpty):
            consumer_0_rx_msgs.get_nowait()

        # Case 4: Send message to unknown subject
        with self.assertRaises(HttpmqAPIError):
            await data_client.publish(
                subject=str(uuid.uuid4()),
                message=str(uuid.uuid4()).encode("utf-8"),
                context=context,
            )

        #############################################################################
        # Stop the three consumer receive loops

        consumer_0_stop.set()
        consumer_1_stop.set()
        consumer_2_stop.set()

        consumer_0_rid = await consumer_0_rx_runner
        consumer_1_rid = await consumer_1_rx_runner
        consumer_2_rid = await consumer_2_rx_runner

        self.assertEqual(consumer_0_rid, consumer_0_runner_context.request_id)
        self.assertEqual(consumer_1_rid, consumer_1_runner_context.request_id)
        self.assertEqual(consumer_2_rid, consumer_2_runner_context.request_id)

        # Delete the stream
        context = RequestContext()
        self.assertEqual(
            context.request_id,
            await mgmt_client.delete_stream(stream=stream_0, context=context),
        )
        with self.assertRaises(HttpmqAPIError):
            await mgmt_client.get_stream(stream=stream_0, context=RequestContext())
