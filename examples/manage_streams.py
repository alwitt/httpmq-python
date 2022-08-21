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
    """Basic example showing how to manage streams with the client."""

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
                max_age=int(timedelta(minutes=1).total_seconds() * 1e9),
            ),
            context=httpmq.RequestContext(),
        )
        log.info("Create stream %s with request %s", stream_name, resp_rid)

        # Read back that stream
        stream_param, resp_rid = await mgmt_client.get_stream(
            stream=stream_name, context=httpmq.RequestContext()
        )
        log.info(
            "Stream %s parameters, read in %s:\n%s",
            stream_name,
            resp_rid,
            json.dumps(stream_param.to_dict(), indent="  "),
        )

        # Change the stream's target subject
        resp_rid = await mgmt_client.change_stream_subjects(
            stream=stream_name,
            new_subjects=["subj.2", "subj.3"],
            context=httpmq.RequestContext(),
        )
        log.info(
            "Changed stream %s's target subjects with request %s", stream_name, resp_rid
        )

        # Read back that stream
        stream_param, resp_rid = await mgmt_client.get_stream(
            stream=stream_name, context=httpmq.RequestContext()
        )
        log.info(
            "Stream %s parameters, read in %s:\n%s",
            stream_name,
            resp_rid,
            json.dumps(stream_param.to_dict(), indent="  "),
        )

        # Change the stream's retention policy
        resp_rid = await mgmt_client.update_stream_limits(
            stream=stream_name,
            limits=httpmq.ManagementJSStreamLimits(
                max_age=int(timedelta(minutes=15).total_seconds() * 1e9)
            ),
            context=httpmq.RequestContext(),
        )
        log.info(
            "Changed stream %s's data retention with request %s", stream_name, resp_rid
        )

        # Read back that stream
        stream_param, resp_rid = await mgmt_client.get_stream(
            stream=stream_name, context=httpmq.RequestContext()
        )
        log.info(
            "Stream %s parameters, read in %s:\n%s",
            stream_name,
            resp_rid,
            json.dumps(stream_param.to_dict(), indent="  "),
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
    """Basic example showing how to manage streams with the client."""
    if verbose:
        httpmq.configure_sdk_logging(global_log_level=logging.DEBUG)
    else:
        httpmq.configure_sdk_logging(global_log_level=logging.INFO)

    log = logging.getLogger("httpmq-sdk.general")

    loop = asyncio.new_event_loop()
    loop.run_until_complete(async_main(log=log))


if __name__ == "__main__":
    main()
