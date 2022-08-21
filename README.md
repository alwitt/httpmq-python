# HTTP MQ - Python Client

Python client for [httpmq](https://github.com/alwitt/httpmq)

[![MIT][License-Image]][License-Url] ![CICD workflow](https://github.com/alwitt/httpmq-python/actions/workflows/cicd.yaml/badge.svg) [![PyPI version](https://badge.fury.io/py/httpmq.svg)](https://badge.fury.io/py/httpmq)

[License-Url]: https://mit-license.org/
[License-Image]: https://img.shields.io/badge/License-MIT-blue.svg

# Table of Content

- [1. Introduction](#1-introduction)
- [2. Installation](#2-installation)
- [3. Examples](#3-examples)
- [4. Local Development](#4-local-development)

---

# [1. Introduction](#table-of-content)

This is a [async](https://docs.python.org/3/library/asyncio.html) Python client SDK for [httpmq](https://github.com/alwitt/httpmq) built around [aiohttp](https://github.com/aio-libs/aiohttp), and uses the auto-generated data models of [httpmq](https://github.com/alwitt/httpmq)'s OpenAPI specification. The auto-generated data models are placed under `httpmq/models`. The module provides client objects for interacting with the management and data plane API of [httpmq](https://github.com/alwitt/httpmq).

```python
import asyncio
import logging
import httpmq


async def async_main(log: logging.Logger):
    try:
        # Create management plane client
        mgmt_client = httpmq.ManagementClient(
            api_client=httpmq.APIClient(base_url="http://127.0.0.1:4100")
        )
        # Create data plane client
        data_client = httpmq.DataClient(
            api_client=httpmq.APIClient(base_url="http://127.0.0.1:4101")
        )

        # Check whether management plane is ready
        await mgmt_client.ready(context=httpmq.RequestContext())
        log.info("Management API ready")

        # Check whether data plane is ready
        await data_client.ready(context=httpmq.RequestContext())
        log.info("Data plane API ready")
    finally:
        # Always disconnect
        await mgmt_client.disconnect()
        await data_client.disconnect()
```

# [2. Installation](#table-of-content)

```shell
$ pip3 install httpmq
```

# [3. Examples](#table-of-content)

- [Hello World](examples/hello_world.md): basic example showing how to define the client.

- [Manage Streams](examples/manage_streams.md): managing streams through the `management` API.

- [Manage Consumers](examples/manage_consumer.md): managing consumers through the `management` API.

- [Sending and Receiving Messages](examples/sending_messages.md): sending and receiving messages.

# [4. Local Development](#table-of-content)

> **NOTE:** Though the described procedures supports local development, the same `docker-compose.yaml` can be used to create a [httpmq](https://github.com/alwitt/httpmq) test environment independent of this project.

This project uses [Poetry](https://python-poetry.org/) as the dependency management framework.

```shell
$ poetry check
All set!
```

A helper Makefile is also included to automate the common development tasks. The available make targets are:

```shell
$ make help
lint                           Run python lint
build                          Build module
test                           Run unit-tests
one-test                       Run specific unit-tests
install                        Install module
uninstall                      Uninstall module
reinstall                      Reinstall module
cli                            Run venv python CLI
compose                        Bring up development environment via docker-compose
clean                          Clean up the python build artifacts
help                           Display this help screen
```

First, prepare the development environment:

```
make
```

This will call `Poetry` to setup the virtual environment, install dependencies, and build the module.

Now, start the development environment:

```shell
$ make compose
docker-compose -f docker-compose.yaml down --volume
Removing network httpmq-python_httpmq-py-test
WARNING: Network httpmq-python_httpmq-py-test not found.
docker-compose -f docker-compose.yaml up -d
Creating network "httpmq-python_httpmq-py-test" with driver "bridge"
Creating httpmq-python_httpmq-data_1 ... done
Creating httpmq-python_httpmq-mgmt_1 ... done
Creating httpmq-python_dev-nats_1    ... done
```

Verify the code passes unit-tests:

```shell
$ make test
poetry run pytest --verbose --junitxml=test-reports/test.xml test/
=============================================== test session starts ===============================================
platform linux -- Python 3.10.6, pytest-7.1.2, pluggy-1.0.0 -- /home/harry/Git/HTTP_Message_Broker/httpmq-python/.venv/bin/python
cachedir: .pytest_cache
rootdir: /home/harry/Git/HTTP_Message_Broker/httpmq-python
collected 11 items

test/test_client.py::TestAPIClient::test_delete PASSED                                                      [  9%]
test/test_client.py::TestAPIClient::test_get PASSED                                                         [ 18%]
test/test_client.py::TestAPIClient::test_post PASSED                                                        [ 27%]
test/test_client.py::TestAPIClient::test_put PASSED                                                         [ 36%]
test/test_client.py::TestAPIClient::test_sse_get PASSED                                                     [ 45%]
test/test_dataplane.py::TestDataplane::test_basic_sanity PASSED                                             [ 54%]
test/test_dataplane.py::TestDataplane::test_message_splitter PASSED                                         [ 63%]
test/test_dataplane.py::TestDataplane::test_push_subscribe PASSED                                           [ 72%]
test/test_management.py::TestManagement::test_basic_sanity PASSED                                           [ 81%]
test/test_management.py::TestManagement::test_consumer_management PASSED                                    [ 90%]
test/test_management.py::TestManagement::test_stream_management PASSED                                      [100%]

----------- generated xml file: /home/harry/Git/HTTP_Message_Broker/httpmq-python/test-reports/test.xml -----------
=============================================== 11 passed in 2.62s ================================================
```

A demo application, `scripts/httpmq_test_cli.py`, is also provided. It exercises all the functionalities of the [httpmq](https://github.com/alwitt/httpmq) APIs. These functionalities are separated into subcommands, and the associated usage message explains how to call each functionality.

> **IMPORTANT:** Before starting, perform
>
> ```shell
> $ make install
> $ poetry shell
> ```
>
> This will install the locally built SDK package into the local virtual environment, and start a new shell within that virtual environment.

```shell
$ ./scripts/httpmq_test_cli.py --help
Usage: httpmq_test_cli.py [OPTIONS] COMMAND [ARGS]...

  Demo application for trying out functionalities of httpmq

Options:
  --custom-ca-file, --ca TEXT  Custom CA file to use with HTTP client  [env
                               var: HTTP_CUSTOM_CA_FILE]
  --access-token, --at TEXT    Bearer access token used for authentication
                               [env var: HTTP_BEARER_ACCESS_TOKEN]
  --request-id, --rid TEXT     Request ID to use with this call  [default:
                               6403e98e-d29a-478b-99e4-49ff07fb210f]
  -v, --verbose                Verbose logging
  --help                       Show this message and exit.

Commands:
  data    Operate the httpmq dataplane API
  manage  Operate the httpmq management API
```

```shell
$ ./scripts/httpmq_test_cli.py manage --help
Usage: httpmq_test_cli.py manage [OPTIONS] COMMAND [ARGS]...

  Operate the httpmq management API

Options:
  -s, --management-server-url TEXT
                                  Management server URL  [env var:
                                  MANAGEMENT_SERVER_URL; default:
                                  http://127.0.0.1:4100]
  --help                          Show this message and exit.

Commands:
  consumer  Manages consumers through httpmq management API
  ready     Verify the management API is ready
  stream    Manages streams through httpmq management API
```

```shell
$ ./scripts/httpmq_test_cli.py manage ready --help
Usage: httpmq_test_cli.py manage ready [OPTIONS]

  Verify the management API is ready

Options:
  --help  Show this message and exit.
```

```shell
$ ./scripts/httpmq_test_cli.py manage stream --help
Usage: httpmq_test_cli.py manage stream [OPTIONS] COMMAND [ARGS]...

  Manages streams through httpmq management API

Options:
  --help  Show this message and exit.

Commands:
  change-retention  Changed a stream's message retention policy.
  change-subject    Changed the target subjects of a stream through management API
  create            Define a new stream through httpmq management API
  delete            Delete one stream through management API
  get               Read information regarding one stream through management API
  list-all          List all streams through httpmq management API
```

```shell
$ ./scripts/httpmq_test_cli.py manage consumer --help
Usage: httpmq_test_cli.py manage consumer [OPTIONS] COMMAND [ARGS]...

  Manages consumers through httpmq management API

Options:
  -s, --target-stream TEXT  Target stream to operate against  [env var:
                            TARGET_STREAM; required]
  --help                    Show this message and exit.

Commands:
  create    Define a new consumer through httpmq management API
  delete    Delete a consumer through httpmq management API
  get       Read information regarding one consumer through management API
  list-all  List all consumers of a stream through httpmq management API
```

```shell
$ ./scripts/httpmq_test_cli.py data --help
Usage: httpmq_test_cli.py data [OPTIONS] COMMAND [ARGS]...

  Operate the httpmq dataplane API

Options:
  -s, --dataplane-server-url TEXT
                                  Dataplane server URL  [env var:
                                  DATAPLANE_SERVER_URL; default:
                                  http://127.0.0.1:4101]
  --help                          Show this message and exit.

Commands:
  pub    Publish messages on a subject through httpmq dataplane API
  ready  Verify the dataplane API is ready
  sub    Subscribe for messages as a consumer on a stream through httpmq dataplane API
```

```shell
$ ./scripts/httpmq_test_cli.py data ready --help
Usage: httpmq_test_cli.py data ready [OPTIONS]

  Verify the dataplane API is ready

Options:
  --help  Show this message and exit.
```
