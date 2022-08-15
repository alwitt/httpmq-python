"""Test bench for httpmq.management"""

from datetime import timedelta
import uuid
import aiohttp
from httpmq.client import APIClient
from httpmq.common import RequestContext, HttpmqAPIError
from httpmq.management import MgmtAPIWrapper
from httpmq.models import ManagementJSStreamParam, ManagementJSStreamLimits
from . import BaseTestCase, async_test, get_unittest_httpmq_mgmt_api_url


class TestManagement(BaseTestCase):
    """Test bench for httpmq.managment"""

    @async_test
    async def test_basic_sanity(self):
        """Basic sanity check of management API client"""

        core_client = APIClient(base_url=get_unittest_httpmq_mgmt_api_url())
        mgmt_client = MgmtAPIWrapper(api_client=core_client)
        await mgmt_client.ready(context=RequestContext())

        another_client = APIClient(base_url="http://127.0.0.1:17881")
        another_mgmt_client = MgmtAPIWrapper(api_client=another_client)
        with self.assertRaises(aiohttp.client_exceptions.ClientConnectorError):
            await another_mgmt_client.ready(context=RequestContext())

    @async_test
    async def test_stream_management(self):
        """Verify stream management"""

        core_client = APIClient(base_url=get_unittest_httpmq_mgmt_api_url())
        mgmt_client = MgmtAPIWrapper(api_client=core_client)
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
