"""Wrapper object for operating the httpmq dataplane API"""

# pylint: disable=too-many-arguments
# pylint: disable=too-few-public-methods
# pylint: disable=too-many-locals


from httpmq.common import RequestContext


class ReceivedMessage:
    """Container for a received message"""

    def __init__(
        self,
        stream: str,
        stream_seq: int,
        consumer: str,
        consumer_seq: int,
        subject: str,
        message: bytes,
        request_id: str,
    ):
        """Constructor

        :param stream: name of the stream this message is from
        :param stream_seq: the message sequence number within this stream
        :param consumer: name of the consumer that received the message
        :param consumer_seq: the message sequence number for that consumer on this stream
        :param subject: the message subject
        :param request_id: request ID
        """
        self.stream = stream
        self.stream_seq = stream_seq
        self.consumer = consumer
        self.consumer_seq = consumer_seq
        self.subject = subject
        self.message = message
        self.request_id = request_id


class DataAPIWrapper:
    """Client wrapper object for operating the httpmq dataplane API"""

    def __init__(self, api_client):
        """Constructor

        :param api_client: base client object for interacting with httpmq
        """

    def ready(self, ctxt: RequestContext):
        """Check whether the httpmq dataplane API is ready. Raise exception if not.

        :param ctxt: the caller context
        """

    def publish(self, subject: str, message: bytes, ctxt: RequestContext) -> str:
        """Publishes a message under a subject

        :param subject: the subject to publish under
        :param message: the message to publish
        :param ctxt: the caller context
        :return: request ID in the response
        """

    def send_ack(
        self,
        stream: str,
        stream_seq: int,
        consumer: str,
        consumer_seq: int,
        ctxt: RequestContext,
    ) -> str:
        """Send a message ACK for an associated JetStream message

        Each message is marked by two sequence numbers.
          * the stream sequence number
          * the consumer sequence number

        The stream sequence number is the global ID of a message within the stream. Each
        message receives a unique monotonically increasing stream sequence number.

        The consumer sequence number tracks the messages sent to a consumer from a stream;
        the consumer has per-stream sequence number tracking for each stream the consumer
        listens to.

        Each time a consumer receives a message from the stream (a new message, or a retransmit
        of a previous message), that consumer's sequence number on that stream is increased.

        :param stream: name of the stream this message is from
        :param stream_seq: the message sequence number within this stream
        :param consumer: name of the consumer that received the message
        :param consumer_seq: the message sequence number for that consumer on this stream
        :param ctxt: the caller context
        :return: request ID in the response
        """

    def push_subscribe(
        self,
        stream: str,
        consumer: str,
        subject_filter: str,
        process_rx_msg_cb,
        ctxt: RequestContext,
        max_msg_inflight: int = None,
        delivery_group: str = None,
    ) -> str:
        """Start a push subscription for a consumer on a stream

        This is a blocking function which only exits when either
          * Connection breaks
          * Server closes the connection

        :param stream: target stream
        :param consumer: consumer name
        :param subject_filter: subscribe for message which subject matches the filter
        :param process_rx_msg_cb: callback function for handling a received message
        :param ctxt: the caller context
        :param max_msg_inflight: the max number of inflight messages if provided
        :param delivery_group: the delivery group the consumer belongs to if the consumer
            uses one
        :return: request ID in the response
        """
