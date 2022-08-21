#!/usr/bin/env python3

"""Example application"""

# pylint: disable=no-value-for-parameter

import asyncio
import logging
import click

from httpmq import configure_sdk_logging
from httpmq.client import APIClient
from httpmq.common import RequestContext
from httpmq.dataplane import DataClient
from httpmq.management import ManagementClient


async def async_main(log: logging.Logger):
    """
    Basic example showing how to define client instances for operating the `management`
    and `dataplane` API.
    """

    try:
        mgmt_client = ManagementClient(
            api_client=APIClient(base_url="http://127.0.0.1:4100")
        )
        await mgmt_client.ready(context=RequestContext())
        log.info("Management API ready")
    finally:
        await mgmt_client.disconnect()

    try:
        data_client = DataClient(api_client=APIClient(base_url="http://127.0.0.1:4101"))
        await data_client.ready(context=RequestContext())
        log.info("Data plane API ready")
    finally:
        await data_client.disconnect()


@click.command()
@click.option("--verbose", "-v", is_flag=True, help="Verbose logging")
def main(verbose: bool):
    """
    Basic example showing how to define client instances for operating the `management`
    and `dataplane` API.
    """
    if verbose:
        configure_sdk_logging(global_log_level=logging.DEBUG)
    else:
        configure_sdk_logging(global_log_level=logging.INFO)

    log = logging.getLogger("httpmq-sdk.general")

    loop = asyncio.new_event_loop()
    loop.run_until_complete(async_main(log=log))


if __name__ == "__main__":
    main()
