# Hello World

Basic example showing how to define client instance for operating the `management` and `dataplane` API.

```python
import asyncio
import logging
import httpmq


async def async_main(log: logging.Logger):
    """
    Basic example showing how to define client instances for operating the `management`
    and `dataplane` API.
    """

    try:
        mgmt_client = httpmq.ManagementClient(
            api_client=httpmq.APIClient(base_url="http://127.0.0.1:4100")
        )
        await mgmt_client.ready(context=httpmq.RequestContext())
        log.info("Management API ready")
    finally:
        await mgmt_client.disconnect()

    try:
        data_client = httpmq.DataClient(
            api_client=httpmq.APIClient(base_url="http://127.0.0.1:4101")
        )
        await data_client.ready(context=httpmq.RequestContext())
        log.info("Data plane API ready")
    finally:
        await data_client.disconnect()
```

> **IMPORTANT:** We define two separate transport clients for reaching `management` and `dataplane` respectively, as they listen on two different URIs.

```shell
$ ./examples/hello_world.py -v
[2022-08-20 14:46:45,086: DEBUG client.py:190 (8510) httpmq-sdk] Defined aiohttp client connecting to 'http://127.0.0.1:4100'
[2022-08-20 14:46:45,086: DEBUG client.py:84 (8510) httpmq-sdk] [9be66eac-dbf0-47ad-aad1-f02daf359239] Request ==>
> GET /v1/admin/ready HTTP/1.1
> Host: 127.0.0.1
> Httpmq-Request-Id: 9be66eac-dbf0-47ad-aad1-f02daf359239
[2022-08-20 14:46:45,088: DEBUG client.py:116 (8510) httpmq-sdk] [9be66eac-dbf0-47ad-aad1-f02daf359239] Response <==
< HTTP/1.1 200 OK
< Content-Type: application/json
< Httpmq-Request-Id: 9be66eac-dbf0-47ad-aad1-f02daf359239
< Date: Sat, 20 Aug 2022 21:46:45 GMT
< Transfer-Encoding: chunked
Request Duration == 1.61 ms
[2022-08-20 14:46:45,088: INFO hello_world.py:25 (8510) httpmq-sdk] Management API ready
[2022-08-20 14:46:45,088: DEBUG client.py:190 (8510) httpmq-sdk] Defined aiohttp client connecting to 'http://127.0.0.1:4101'
[2022-08-20 14:46:45,089: DEBUG client.py:84 (8510) httpmq-sdk] [eedec754-6ae8-421a-94bb-1f3e706fa7e8] Request ==>
> GET /v1/data/ready HTTP/1.1
> Host: 127.0.0.1
> Httpmq-Request-Id: eedec754-6ae8-421a-94bb-1f3e706fa7e8
[2022-08-20 14:46:45,089: DEBUG client.py:116 (8510) httpmq-sdk] [eedec754-6ae8-421a-94bb-1f3e706fa7e8] Response <==
< HTTP/1.1 200 OK
< Content-Type: application/json
< Httpmq-Request-Id: eedec754-6ae8-421a-94bb-1f3e706fa7e8
< Date: Sat, 20 Aug 2022 21:46:45 GMT
< Transfer-Encoding: chunked
Request Duration == 0.945 ms
[2022-08-20 14:46:45,090: INFO hello_world.py:34 (8510) httpmq-sdk] Data plane API ready
```
