#!/usr/bin/env python3

"""Example application"""

# pylint: disable=no-value-for-parameter

import asyncio
from datetime import timedelta
import json
import logging
import uuid
import click
import httpmq


async def async_main(log: logging.Logger):
    """Basic example showing how to manage consumers with the client."""
    try:
        # Define httpmq management API client
        mgmt_client = httpmq.ManagementClient(
            api_client=httpmq.APIClient(base_url="http://127.0.0.1:4100")
        )
        await mgmt_client.ready(context=httpmq.RequestContext())
        log.info("Management API ready")

        # Define a stream
        stream_name = str(uuid.uuid4())
        resp_rid = await mgmt_client.create_stream(
            params=httpmq.ManagementJSStreamParam(
                name=stream_name,
                subjects=["subj.1", "subj.2"],
                max_age=int(timedelta(minutes=10).total_seconds() * 1e9),
            ),
            context=httpmq.RequestContext(),
        )
        log.info("Create stream %s with request %s", stream_name, resp_rid)

        # Define a consumer
        consumer_name = str(uuid.uuid4())
        resp_rid = await mgmt_client.create_consumer_for_stream(
            stream=stream_name,
            params=httpmq.ManagementJetStreamConsumerParam(
                name=consumer_name, mode="push", max_inflight=1
            ),
            context=httpmq.RequestContext(),
        )
        log.info("Create consumer %s with request %s", consumer_name, resp_rid)

        # Read the consumer back
        consumer_param, resp_rid = await mgmt_client.get_consumer_of_stream(
            stream=stream_name,
            consumer=consumer_name,
            context=httpmq.RequestContext(),
        )
        log.info(
            "Consumer %s parameters, read in %s:\n%s",
            stream_name,
            resp_rid,
            json.dumps(consumer_param.to_dict(), indent="  "),
        )

        # Delete the stream
        resp_rid = await mgmt_client.delete_stream(
            stream=stream_name, context=httpmq.RequestContext()
        )
        log.info("Deleted stream %s with request %s", stream_name, resp_rid)
    finally:
        await mgmt_client.disconnect()


@click.command()
@click.option("--verbose", "-v", is_flag=True, help="Verbose logging")
def main(verbose: bool):
    """Basic example showing how to manage consumers with the client."""
    if verbose:
        httpmq.configure_sdk_logging(global_log_level=logging.DEBUG)
    else:
        httpmq.configure_sdk_logging(global_log_level=logging.INFO)

    log = logging.getLogger("httpmq-sdk.general")

    loop = asyncio.new_event_loop()
    loop.run_until_complete(async_main(log=log))


if __name__ == "__main__":
    main()
