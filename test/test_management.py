"""Test bench for httpmq.management"""

# pylint: disable=too-many-locals
# pylint: disable=too-many-statements

from datetime import timedelta
import uuid
import aiohttp
from httpmq.client import APIClient
from httpmq.common import RequestContext, HttpmqAPIError
from httpmq.management import ManagementClient
from httpmq.models import (
    ManagementJetStreamConsumerParam,
    ManagementJSStreamLimits,
    ManagementJSStreamParam,
)
from . import BaseTestCase, async_test, get_unittest_httpmq_mgmt_api_url


class TestManagement(BaseTestCase):
    """Test bench for httpmq.managment"""

    @async_test
    async def test_basic_sanity(self):
        """Basic sanity check of management API client"""

        core_client = APIClient(base_url=get_unittest_httpmq_mgmt_api_url())
        mgmt_client = ManagementClient(api_client=core_client)
        await mgmt_client.ready(context=RequestContext())

        another_client = APIClient(base_url="http://127.0.0.1:17881")
        another_mgmt_client = ManagementClient(api_client=another_client)
        with self.assertRaises(aiohttp.client_exceptions.ClientConnectorError):
            await another_mgmt_client.ready(context=RequestContext())

    @async_test
    async def test_stream_management(self):
        """Verify stream management"""

        mgmt_client = ManagementClient(
            api_client=APIClient(base_url=get_unittest_httpmq_mgmt_api_url())
        )
        await mgmt_client.ready(context=RequestContext())

        # Case 0: create a stream
        stream_0 = str(uuid.uuid4())
        subjects_0 = [str(uuid.uuid4())]
        stream_0_param = ManagementJSStreamParam(name=stream_0, subjects=subjects_0)
        context = RequestContext()
        self.assertEqual(
            context.request_id,
            await mgmt_client.create_stream(params=stream_0_param, context=context),
        )

        # Case 1: create the same stream again
        context = RequestContext()
        self.assertEqual(
            context.request_id,
            await mgmt_client.create_stream(params=stream_0_param, context=context),
        )

        # Case 2: create another stream but with same subject
        stream_2_param = ManagementJSStreamParam(
            name=str(uuid.uuid4()), subjects=subjects_0
        )
        with self.assertRaises(HttpmqAPIError):
            await mgmt_client.create_stream(
                params=stream_2_param, context=RequestContext()
            )

        # Case 3: read back the stream info
        context = RequestContext()
        stream_0_rb, rid = await mgmt_client.get_stream(
            stream=stream_0, context=context
        )
        self.assertEqual(rid, context.request_id)
        self.assertEqual(stream_0_rb.config.name, stream_0)
        self.assertListEqual(stream_0_rb.config.subjects, subjects_0)
        context = RequestContext()
        all_streams, rid = await mgmt_client.list_all_streams(context=context)
        self.assertEqual(rid, context.request_id)
        self.assertIn(stream_0, all_streams)
        stream_rb = all_streams[stream_0]
        self.assertEqual(stream_rb.config.name, stream_0)
        self.assertListEqual(stream_rb.config.subjects, subjects_0)

        # Case 4: alter subjects for stream
        subjects_4 = [str(uuid.uuid4()), str(uuid.uuid4())]
        context = RequestContext()
        self.assertEqual(
            context.request_id,
            await mgmt_client.change_stream_subjects(
                stream=stream_0, new_subjects=subjects_4, context=context
            ),
        )
        context = RequestContext()
        stream_0_rb, rid = await mgmt_client.get_stream(
            stream=stream_0, context=context
        )
        self.assertEqual(rid, context.request_id)
        self.assertEqual(stream_0_rb.config.name, stream_0)
        self.assertListEqual(stream_0_rb.config.subjects, subjects_4)

        # Case 5: alter stream data retention
        new_max_age = int(timedelta(hours=1).total_seconds() * 1e9)
        new_limits = ManagementJSStreamLimits(max_age=new_max_age)
        context = RequestContext()
        self.assertEqual(
            context.request_id,
            await mgmt_client.update_stream_limits(
                stream=stream_0, limits=new_limits, context=context
            ),
        )
        context = RequestContext()
        stream_0_rb, rid = await mgmt_client.get_stream(
            stream=stream_0, context=context
        )
        self.assertEqual(rid, context.request_id)
        self.assertEqual(stream_0_rb.config.name, stream_0)
        self.assertEqual(stream_0_rb.config.max_age, new_max_age)

        # Case 6: delete the stream
        context = RequestContext()
        self.assertEqual(
            context.request_id,
            await mgmt_client.delete_stream(stream=stream_0, context=context),
        )
        with self.assertRaises(HttpmqAPIError):
            await mgmt_client.get_stream(stream=stream_0, context=RequestContext())

    @async_test
    async def test_consumer_management(self):
        """Verify consumer management"""

        mgmt_client = ManagementClient(
            api_client=APIClient(base_url=get_unittest_httpmq_mgmt_api_url())
        )
        await mgmt_client.ready(context=RequestContext())

        # Case 0: create consumer with unknown stream
        consumer_param = ManagementJetStreamConsumerParam(
            name=str(uuid.uuid4()),
            mode="push",
            max_inflight=2,
            filter_subject=str(uuid.uuid4()),
        )
        with self.assertRaises(HttpmqAPIError):
            await mgmt_client.create_consumer_for_stream(
                stream=str(uuid.uuid4()),
                params=consumer_param,
                context=RequestContext(),
            )

        # Case 1: create a stream
        stream_1 = str(uuid.uuid4())
        subject_base = str(uuid.uuid4())
        subjects_1 = [f"{subject_base}.a", f"{subject_base}.b"]
        stream_1_param = ManagementJSStreamParam(name=stream_1, subjects=subjects_1)
        context = RequestContext()
        self.assertEqual(
            context.request_id,
            await mgmt_client.create_stream(params=stream_1_param, context=context),
        )
        context = RequestContext()
        stream_1_rb, rid = await mgmt_client.get_stream(
            stream=stream_1, context=context
        )
        self.assertEqual(rid, context.request_id)
        self.assertEqual(stream_1_rb.config.name, stream_1)
        self.assertListEqual(stream_1_rb.config.subjects, subjects_1)

        # Case 2: create a consumer on stream
        consumer_2 = str(uuid.uuid4())
        consumer_param = ManagementJetStreamConsumerParam(
            name=consumer_2,
            mode="push",
            max_inflight=1,
            filter_subject=subjects_1[0],
        )
        context = RequestContext()
        self.assertEqual(
            context.request_id,
            await mgmt_client.create_consumer_for_stream(
                stream=stream_1, params=consumer_param, context=context
            ),
        )

        # Case 3: create same consumer again on stream
        context = RequestContext()
        self.assertEqual(
            context.request_id,
            await mgmt_client.create_consumer_for_stream(
                stream=stream_1, params=consumer_param, context=context
            ),
        )

        # Case 4: create same consumer with different subject
        consumer_param = ManagementJetStreamConsumerParam(
            name=consumer_2,
            mode="push",
            max_inflight=1,
            filter_subject=subjects_1[1],
        )
        with self.assertRaises(HttpmqAPIError):
            await mgmt_client.create_consumer_for_stream(
                stream=stream_1, params=consumer_param, context=RequestContext()
            )

        # Case 5: create consumer against unknown subject
        consumer_param = ManagementJetStreamConsumerParam(
            name=str(uuid.uuid4()),
            mode="push",
            max_inflight=1,
            filter_subject=str(uuid.uuid4()),
        )
        with self.assertRaises(HttpmqAPIError):
            await mgmt_client.create_consumer_for_stream(
                stream=stream_1, params=consumer_param, context=RequestContext()
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
        context = RequestContext()
        self.assertEqual(
            context.request_id,
            await mgmt_client.create_consumer_for_stream(
                stream=stream_1, params=consumer_param, context=context
            ),
        )

        # Case 7: read back consumer info
        context = RequestContext()
        consumer_2_rb, rid = await mgmt_client.get_consumer_of_stream(
            stream=stream_1, consumer=consumer_2, context=context
        )
        self.assertEqual(rid, context.request_id)
        self.assertEqual(consumer_2_rb.config.max_ack_pending, 1)
        self.assertEqual(consumer_2_rb.config.filter_subject, subjects_1[0])
        context = RequestContext()
        all_consumers, rid = await mgmt_client.list_all_consumer_of_stream(
            stream=stream_1, context=context
        )
        self.assertEqual(rid, context.request_id)
        self.assertEqual(len(all_consumers), 2)
        self.assertIn(consumer_6, all_consumers)
        consumer_6_rb = all_consumers[consumer_6]
        self.assertEqual(consumer_6_rb.config.max_ack_pending, 2)
        self.assertEqual(consumer_6_rb.config.filter_subject, subject_6)

        # Case 8: delete the consumer
        context = RequestContext()
        self.assertEqual(
            context.request_id,
            await mgmt_client.delete_consumer_on_stream(
                stream=stream_1, consumer=consumer_2, context=context
            ),
        )
        context = RequestContext()
        self.assertEqual(
            context.request_id,
            await mgmt_client.delete_consumer_on_stream(
                stream=stream_1, consumer=consumer_6, context=context
            ),
        )
        context = RequestContext()
        all_consumers, rid = await mgmt_client.list_all_consumer_of_stream(
            stream=stream_1, context=context
        )
        self.assertEqual(rid, context.request_id)
        self.assertEqual(len(all_consumers), 0)

        # Delete the stream
        context = RequestContext()
        self.assertEqual(
            context.request_id,
            await mgmt_client.delete_stream(stream=stream_1, context=context),
        )
        with self.assertRaises(HttpmqAPIError):
            await mgmt_client.get_stream(stream=stream_1, context=RequestContext())
