#!/usr/bin/env python3

"""Example application"""

# pylint: disable=no-value-for-parameter

import asyncio
from datetime import timedelta
import json
import logging
import uuid
import click

from httpmq import configure_sdk_logging
from httpmq.client import APIClient
from httpmq.common import RequestContext
from httpmq.management import ManagementClient
from httpmq.models import ManagementJSStreamParam, ManagementJetStreamConsumerParam


async def async_main(log: logging.Logger):
    """Basic example showing how to manage consumers with the client."""
    try:
        # Define httpmq management API client
        mgmt_client = ManagementClient(
            api_client=APIClient(base_url="http://127.0.0.1:4100")
        )
        await mgmt_client.ready(context=RequestContext())
        log.info("Management API ready")

        # Define a stream
        stream_name = str(uuid.uuid4())
        resp_rid = await mgmt_client.create_stream(
            params=ManagementJSStreamParam(
                name=stream_name,
                subjects=["subj.1", "subj.2"],
                max_age=int(timedelta(minutes=10).total_seconds() * 1e9),
            ),
            context=RequestContext(),
        )
        log.info("Create stream %s with request %s", stream_name, resp_rid)

        # Define a consumer
        consumer_name = str(uuid.uuid4())
        resp_rid = await mgmt_client.create_consumer_for_stream(
            stream=stream_name,
            params=ManagementJetStreamConsumerParam(
                name=consumer_name, mode="push", max_inflight=1
            ),
            context=RequestContext(),
        )
        log.info("Create consumer %s with request %s", consumer_name, resp_rid)

        # Read the consumer back
        consumer_param, resp_rid = await mgmt_client.get_consumer_of_stream(
            stream=stream_name,
            consumer=consumer_name,
            context=RequestContext(),
        )
        log.info(
            "Consumer %s parameters, read in %s:\n%s",
            stream_name,
            resp_rid,
            json.dumps(consumer_param.to_dict(), indent="  "),
        )

        # Delete the stream
        resp_rid = await mgmt_client.delete_stream(
            stream=stream_name, context=RequestContext()
        )
        log.info("Deleted stream %s with request %s", stream_name, resp_rid)
    finally:
        await mgmt_client.disconnect()


@click.command()
@click.option("--verbose", "-v", is_flag=True, help="Verbose logging")
def main(verbose: bool):
    """Basic example showing how to manage consumers with the client."""
    if verbose:
        configure_sdk_logging(global_log_level=logging.DEBUG)
    else:
        configure_sdk_logging(global_log_level=logging.INFO)

    log = logging.getLogger("httpmq-sdk.general")

    loop = asyncio.new_event_loop()
    loop.run_until_complete(async_main(log=log))


if __name__ == "__main__":
    main()
