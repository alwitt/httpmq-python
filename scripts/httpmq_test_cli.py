#!/usr/bin/env python3

"""HTTP MQ demo application"""

# pylint: disable=no-value-for-parameter
# pylint: disable=broad-except
# pylint: disable=function-redefined

import asyncio
from datetime import timedelta
import json
import logging
from pathlib import Path
import ssl
import traceback
from typing import List
import uuid
import click

from httpmq import configure_sdk_logging
from httpmq.client import APIClient
from httpmq.common import RequestContext
from httpmq.management import MgmtAPIWrapper
from httpmq.models import (
    ManagementJSStreamParam,
    ManagementJSStreamLimits,
    ManagementJetStreamConsumerParam,
)


@click.group(context_settings={"show_default": True})
@click.option(
    "--custom-ca-file",
    "--ca",
    required=False,
    envvar="HTTP_CUSTOM_CA_FILE",
    show_envvar=True,
    help="Custom CA file to use with HTTP client",
)
@click.option(
    "--access-token",
    "--at",
    required=False,
    envvar="HTTP_BEARER_ACCESS_TOKEN",
    show_envvar=True,
    help="Bearer access token used for authentication",
)
@click.option(
    "--request-id",
    "--rid",
    default=str(uuid.uuid4()),
    help="Request ID to use with this call",
)
@click.option("--verbose", "-v", is_flag=True, help="Verbose logging")
@click.pass_context
def cli(ctx, custom_ca_file: str, access_token: str, request_id: str, verbose: bool):
    """Demo application for trying out functionalities of httpmq"""
    ctx.ensure_object(dict)

    if verbose:
        configure_sdk_logging(global_log_level=logging.DEBUG)
    else:
        configure_sdk_logging(global_log_level=logging.INFO)

    ctx.obj["logger"] = logging.getLogger("httpmq-sdk.general")

    ctx.obj["asyncio_loop"] = asyncio.new_event_loop()

    if custom_ca_file is not None and Path(custom_ca_file).exists():
        sslcontext = ssl.create_default_context(cafile=custom_ca_file)
        ctx.obj["custom_ca"] = sslcontext
    else:
        ctx.obj["custom_ca"] = None

    request_context = RequestContext()
    request_context.set_request_id(request_id=request_id)

    if access_token is not None:
        request_context.add_header_auth_token(f"Bearer {access_token}")

    ctx.obj["context"] = request_context


################################################################################################
#
# HTTP MQ Management
#
################################################################################################


@cli.group()
@click.option(
    "--management-server-url",
    "-s",
    default="http://127.0.0.1:4100",
    envvar="MANAGEMENT_SERVER_URL",
    show_envvar=True,
    help="Management server URL",
)
@click.pass_context
def management(ctx, management_server_url: str):
    """Operate the httpmq management API"""
    ctx.obj["url"] = management_server_url


def define_management_client(ctx) -> MgmtAPIWrapper:
    """Define a management API wrapper client"""
    api_client = APIClient(
        base_url=ctx.obj["url"],
        ssl_context=ctx.obj["custom_ca"],
    )
    return MgmtAPIWrapper(api_client=api_client)


@management.command()
@click.pass_context
def ready(ctx):
    """Verify the management API is ready"""
    log = ctx.obj["logger"]

    async def core_func():
        """Core logic"""
        mgmt_client: MgmtAPIWrapper = define_management_client(ctx)
        try:
            await mgmt_client.ready(ctx.obj["context"])
            log.info("Management API Ready")
        except Exception as err:
            log.error(
                "".join(traceback.format_exception(type(err), err, err.__traceback__))
            )
        await mgmt_client.disconnect()

    ctx.obj["asyncio_loop"].run_until_complete(core_func())


################################################################################################
# Stream management


@management.group()
@click.pass_context
def stream(_):
    """Manages streams through httpmq management API"""


@stream.command()
@click.option("--name", "-n", required=True, help="JetStream stream name")
@click.option(
    "--subjects",
    "-s",
    required=False,
    multiple=True,
    help="Target subjects for the stream. If not set, the name will be the target.",
)
@click.option(
    "--max-message-age-hours",
    "-o",
    type=float,
    default=1.0,
    help="For data retention, the max duration in HOURS a message is kept in the stream.",
)
@click.pass_context
def create(ctx, name: str, subjects: List[str], max_message_age_hours: float):
    """Define a new stream through httpmq management API"""
    log = ctx.obj["logger"]

    async def core_func():
        """Core logic"""
        mgmt_client: MgmtAPIWrapper = define_management_client(ctx)
        params = ManagementJSStreamParam(
            name=name,
            subjects=subjects if subjects else [name],
            max_age=int(timedelta(hours=max_message_age_hours).total_seconds() * 1e9),
        )
        try:
            resp_rid = await mgmt_client.create_stream(
                params=params, context=ctx.obj["context"]
            )
            log.debug("Returned request-id '%s'", resp_rid)
        except Exception as err:
            log.error(
                "".join(traceback.format_exception(type(err), err, err.__traceback__))
            )
        await mgmt_client.disconnect()

    ctx.obj["asyncio_loop"].run_until_complete(core_func())


@stream.command()
@click.pass_context
def list_all(ctx):
    """List all streams through httpmq management API"""
    log = ctx.obj["logger"]

    async def core_func():
        """Core logic"""
        mgmt_client: MgmtAPIWrapper = define_management_client(ctx)
        try:
            all_streams, resp_rid = await mgmt_client.list_all_streams(
                context=ctx.obj["context"]
            )
            log.debug("Returned request-id '%s'", resp_rid)
            # Convert the result
            for_output = {
                stream_name: stream_param.to_dict()
                for stream_name, stream_param in all_streams.items()
            }
            log.info("Available streams:\n%s", json.dumps(for_output, indent="  "))
        except Exception as err:
            log.error(
                "".join(traceback.format_exception(type(err), err, err.__traceback__))
            )
        await mgmt_client.disconnect()

    ctx.obj["asyncio_loop"].run_until_complete(core_func())


@stream.command()
@click.option("--name", "-n", required=True, help="JetStream stream name")
@click.pass_context
def get(ctx, name: str):
    """Read information regarding one stream through management API"""
    log = ctx.obj["logger"]

    async def core_func():
        """Core logic"""
        mgmt_client: MgmtAPIWrapper = define_management_client(ctx)
        try:
            one_stream, resp_rid = await mgmt_client.get_stream(
                stream=name, context=ctx.obj["context"]
            )
            log.debug("Returned request-id '%s'", resp_rid)
            log.info(
                "Stream %s:\n%s", name, json.dumps(one_stream.to_dict(), indent="  ")
            )
        except Exception as err:
            log.error(
                "".join(traceback.format_exception(type(err), err, err.__traceback__))
            )
        await mgmt_client.disconnect()

    ctx.obj["asyncio_loop"].run_until_complete(core_func())


@stream.command()
@click.option("--name", "-n", required=True, help="JetStream stream name")
@click.pass_context
def delete(ctx, name: str):
    """Delete one stream through management API"""
    log = ctx.obj["logger"]

    async def core_func():
        """Core logic"""
        mgmt_client: MgmtAPIWrapper = define_management_client(ctx)
        try:
            resp_rid = await mgmt_client.delete_stream(
                stream=name, context=ctx.obj["context"]
            )
            log.debug("Returned request-id '%s'", resp_rid)
        except Exception as err:
            log.error(
                "".join(traceback.format_exception(type(err), err, err.__traceback__))
            )
        await mgmt_client.disconnect()

    ctx.obj["asyncio_loop"].run_until_complete(core_func())


@stream.command()
@click.option("--name", "-n", required=True, help="JetStream stream name")
@click.option(
    "--subjects",
    "-s",
    required=True,
    multiple=True,
    help="Target subjects for the stream",
)
@click.pass_context
def change_subject(ctx, name: str, subjects: List[str]):
    """Changed the target subjects of a stream through management API"""
    log = ctx.obj["logger"]

    async def core_func():
        """Core logic"""
        mgmt_client: MgmtAPIWrapper = define_management_client(ctx)
        try:
            resp_rid = await mgmt_client.change_stream_subjects(
                stream=name, new_subjects=subjects, context=ctx.obj["context"]
            )
            log.debug("Returned request-id '%s'", resp_rid)
        except Exception as err:
            log.error(
                "".join(traceback.format_exception(type(err), err, err.__traceback__))
            )
        await mgmt_client.disconnect()

    ctx.obj["asyncio_loop"].run_until_complete(core_func())


@stream.command()
@click.option("--name", "-n", required=True, help="JetStream stream name")
@click.option(
    "--max-message-age-hours",
    "-o",
    type=float,
    default=1.0,
    help="For data retention, the max duration in HOURS a message is kept in the stream.",
)
@click.pass_context
def change_retention(ctx, name: str, max_message_age_hours: float):
    """Changed a stream's message retention policy. Only exposed message age here."""
    log = ctx.obj["logger"]

    async def core_func():
        """Core logic"""
        mgmt_client: MgmtAPIWrapper = define_management_client(ctx)
        new_limits = ManagementJSStreamLimits(
            max_age=int(timedelta(hours=max_message_age_hours).total_seconds() * 1e9),
        )
        try:
            resp_rid = await mgmt_client.update_stream_limits(
                stream=name, limits=new_limits, context=ctx.obj["context"]
            )
            log.debug("Returned request-id '%s'", resp_rid)
        except Exception as err:
            log.error(
                "".join(traceback.format_exception(type(err), err, err.__traceback__))
            )
        await mgmt_client.disconnect()

    ctx.obj["asyncio_loop"].run_until_complete(core_func())


################################################################################################
# Consumer management


@management.group()
@click.option(
    "--target-stream",
    "-s",
    required=True,
    envvar="TARGET_STREAM",
    show_envvar=True,
    help="Target stream to operate against",
)
@click.pass_context
def consumer(ctx, target_stream: str):
    """Manages consumers through httpmq management API"""
    ctx.obj["target_stream"] = target_stream


@consumer.command()
@click.option("--name", "-n", required=True, help="JetStream consumer name")
@click.option("--subject-filter", "-s", required=True, help="Target subject filter")
@click.option(
    "--max-inflight",
    "-m",
    type=int,
    default=1,
    help="Max number of inflight / unACKed messages allowed at once",
)
@click.option("--delivery-group", "-g", required=False, help="Consumer delivery group")
@click.pass_context
def create(
    ctx, name: str, subject_filter: str, max_inflight: int, delivery_group: str = None
):
    """Define a new consumer through httpmq management API"""
    log = ctx.obj["logger"]

    async def core_func():
        """Core logic"""
        mgmt_client: MgmtAPIWrapper = define_management_client(ctx)
        params = ManagementJetStreamConsumerParam(
            name=name,
            mode="push",
            filter_subject=subject_filter,
            max_inflight=max_inflight,
            delivery_group=delivery_group,
        )
        try:
            resp_rid = await mgmt_client.create_consumer_for_stream(
                stream=ctx.obj["target_stream"],
                params=params,
                context=ctx.obj["context"],
            )
            log.debug("Returned request-id '%s'", resp_rid)
        except Exception as err:
            log.error(
                "".join(traceback.format_exception(type(err), err, err.__traceback__))
            )
        await mgmt_client.disconnect()

    ctx.obj["asyncio_loop"].run_until_complete(core_func())


@consumer.command()
@click.pass_context
def list_all(ctx):
    """List all consumers of a stream through httpmq management API"""
    log = ctx.obj["logger"]

    async def core_func():
        """Core logic"""
        mgmt_client: MgmtAPIWrapper = define_management_client(ctx)
        try:
            all_consumers, resp_rid = await mgmt_client.list_all_consumer_of_stream(
                stream=ctx.obj["target_stream"],
                context=ctx.obj["context"],
            )
            log.debug("Returned request-id '%s'", resp_rid)
            # Convert the result
            for_output = {
                consumer_name: consumer_param.to_dict()
                for consumer_name, consumer_param in all_consumers.items()
            }
            log.info("Available consumer:\n%s", json.dumps(for_output, indent="  "))
        except Exception as err:
            log.error(
                "".join(traceback.format_exception(type(err), err, err.__traceback__))
            )
        await mgmt_client.disconnect()

    ctx.obj["asyncio_loop"].run_until_complete(core_func())


@consumer.command()
@click.option("--name", "-n", required=True, help="JetStream consumer name")
@click.pass_context
def get(ctx, name: str):
    """Read information regarding one consumer through management API"""
    log = ctx.obj["logger"]

    async def core_func():
        """Core logic"""
        mgmt_client: MgmtAPIWrapper = define_management_client(ctx)
        try:
            one_consumer, resp_rid = await mgmt_client.get_consumer_of_stream(
                stream=ctx.obj["target_stream"],
                context=ctx.obj["context"],
                consumer=name,
            )
            log.debug("Returned request-id '%s'", resp_rid)
            log.info(
                "Consumer %s:\n%s",
                name,
                json.dumps(one_consumer.to_dict(), indent="  "),
            )
        except Exception as err:
            log.error(
                "".join(traceback.format_exception(type(err), err, err.__traceback__))
            )
        await mgmt_client.disconnect()

    ctx.obj["asyncio_loop"].run_until_complete(core_func())


@consumer.command()
@click.option("--name", "-n", required=True, help="JetStream consumer name")
@click.pass_context
def delete(ctx, name: str):
    """Delete a consumer through httpmq management API"""
    log = ctx.obj["logger"]

    async def core_func():
        """Core logic"""
        mgmt_client: MgmtAPIWrapper = define_management_client(ctx)
        try:
            resp_rid = await mgmt_client.delete_consumer_on_stream(
                stream=ctx.obj["target_stream"],
                consumer=name,
                context=ctx.obj["context"],
            )
            log.debug("Returned request-id '%s'", resp_rid)
        except Exception as err:
            log.error(
                "".join(traceback.format_exception(type(err), err, err.__traceback__))
            )
        await mgmt_client.disconnect()

    ctx.obj["asyncio_loop"].run_until_complete(core_func())


if __name__ == "__main__":
    cli()
