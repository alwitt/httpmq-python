#!/usr/bin/env python3

"""Example application"""

# pylint: disable=no-value-for-parameter

import asyncio
from datetime import timedelta
import logging
from typing import Union
import uuid
import click
import httpmq


async def async_main(log: logging.Logger):
    """Basic example showing how to publish and subscribe for messages."""
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
                subjects=["subj.1"],
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

        # Define httpmq dataplane API client
        data_client = httpmq.DataClient(
            api_client=httpmq.APIClient(base_url="http://127.0.0.1:4101")
        )
        await data_client.ready(context=httpmq.RequestContext())
        log.info("Data plane API ready")

        # Start push-subscribe read loop
        rx_task_stop = asyncio.Event()
        rx_msg_queue = asyncio.Queue()

        async def handle_msg(msg: Union[httpmq.ReceivedMessage, httpmq.HttpmqAPIError]):
            """Callback function to process the messages"""
            if not isinstance(msg, (httpmq.ReceivedMessage, httpmq.HttpmqAPIError)):
                raise RuntimeError(
                    f"Received unknown message type from push_subscribe: {type(msg)}"
                )
            await rx_msg_queue.put(msg)

        # Start receiving messages
        rx_task = asyncio.create_task(
            data_client.push_subscribe(
                stream=stream_name,
                consumer=consumer_name,
                subject_filter="subj.1",
                forward_data_cb=handle_msg,
                stop_loop=rx_task_stop,
                max_msg_inflight=1,
                context=httpmq.RequestContext(),
            )
        )

        # Publish a message
        message = f"Hello world {str(uuid.uuid4())}"
        resp_rid = await data_client.publish(
            subject="subj.1",
            message=message.encode("utf-8"),
            context=httpmq.RequestContext(),
        )
        log.info("Published message '%s' to 'subj.1' in request %s", message, resp_rid)

        # Wait for message to be read
        rx_msg = await rx_msg_queue.get()
        rx_msg_queue.task_done()
        if not isinstance(rx_msg, httpmq.ReceivedMessage):
            raise RuntimeError(
                f"Received unknown message type from push_subscribe: {type(rx_msg)}"
            )
        log.info("Read: '%s'", rx_msg.message.decode("utf-8"))

        # ACK the message
        resp_rid = await data_client.send_ack_simple(
            original_msg=rx_msg,
            context=httpmq.RequestContext(),
        )
        log.info("ACKed message in request %s", resp_rid)

        # Stop the RX loop
        rx_task_stop.set()
        resp_rid = await rx_task
        log.info("Push-subscribe request ID is %s", resp_rid)

        # Delete the stream
        resp_rid = await mgmt_client.delete_stream(
            stream=stream_name, context=httpmq.RequestContext()
        )
        log.info("Deleted stream %s with request %s", stream_name, resp_rid)
    finally:
        await mgmt_client.disconnect()
        await data_client.disconnect()


@click.command()
@click.option("--verbose", "-v", is_flag=True, help="Verbose logging")
def main(verbose: bool):
    """Basic example showing how to publish and subscribe for messages."""
    if verbose:
        httpmq.configure_sdk_logging(global_log_level=logging.DEBUG)
    else:
        httpmq.configure_sdk_logging(global_log_level=logging.INFO)

    log = logging.getLogger("httpmq-sdk.general")

    loop = asyncio.new_event_loop()
    loop.run_until_complete(async_main(log=log))


if __name__ == "__main__":
    main()
