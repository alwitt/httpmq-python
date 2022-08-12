"""HTTP MQ - Python Client"""

# pylint: disable=too-many-arguments

import logging

DEFAULT_REQUEST_ID_FIELD = "Httpmq-Request-Id"


def configure_sdk_logging(
    global_log_format: str = (
        "[%(asctime)s: %(levelname)s %(filename)s:%(lineno)d (%(process)d) httpmq-sdk] %(message)s"
    ),
    global_log_level: int = logging.WARNING,
    management_log_format: str = None,
    management_log_level: int = None,
    dataplane_log_format: str = None,
    dataplane_log_level: int = None,
    http_client_log_format: str = None,
    http_client_log_level: int = None,
):
    """Configure log setting for SDK

    :param global_log_format: log format for the whole SDK if per module format not defined
    :param global_log_level: log level for the whole SDK if per module level not defined
    :param management_log_format: log format for the management module
    :param management_log_level: log level for the management module
    :param dataplane_log_format: log format for the dataplane module
    :param dataplane_log_level: log level for the dataplane module
    :param http_client_log_format: log format for the HTTP client module
    :param http_client_log_level: log level for the HTTP client module
    """

    # Override module level setting if None provided
    if management_log_format is None:
        management_log_format = global_log_format
    if management_log_level is None:
        management_log_level = global_log_level
    if dataplane_log_format is None:
        dataplane_log_format = global_log_format
    if dataplane_log_level is None:
        dataplane_log_level = global_log_level
    if http_client_log_format is None:
        http_client_log_format = global_log_format
    if http_client_log_level is None:
        http_client_log_level = global_log_level

    # Set up the loggers
    for param_set in [
        {
            "name": "httpmq-sdk.general",
            "format": global_log_format,
            "level": global_log_level,
        },
        {
            "name": "httpmq-sdk.client",
            "format": http_client_log_format,
            "level": http_client_log_level,
        },
        {
            "name": "httpmq-sdk.management",
            "format": management_log_format,
            "level": management_log_level,
        },
        {
            "name": "httpmq-sdk.dataplane",
            "format": dataplane_log_format,
            "level": dataplane_log_level,
        },
    ]:
        logger = logging.getLogger(param_set["name"])
        logger.handlers = []
        log_handler = logging.StreamHandler()
        log_format = logging.Formatter(param_set["format"])
        log_handler.setFormatter(log_format)
        log_handler.setLevel(param_set["level"])
        logger.setLevel(param_set["level"])
        logger.addHandler(log_handler)
