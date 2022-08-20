# Manage Consumers

Basic example showing how to manage consumers with the client.

```shell
$ ./examples/manage_consumer.py
[2022-08-20 15:51:33,113: INFO manage_consumer.py:29 (13129) httpmq-sdk] Management API ready
[2022-08-20 15:51:33,116: INFO manage_consumer.py:41 (13129) httpmq-sdk] Create stream ba59220f-58fc-4f33-a7fd-dfa9134afa8d with request f98c227e-08a4-4999-a00b-9b78832f4f8d
[2022-08-20 15:51:33,118: INFO manage_consumer.py:52 (13129) httpmq-sdk] Create consumer 5dc371f4-0da8-40e7-baca-a85529e51a22 with request 631fd1f3-4208-4524-b645-2268e6a20355
[2022-08-20 15:51:33,120: INFO manage_consumer.py:60 (13129) httpmq-sdk] Consumer ba59220f-58fc-4f33-a7fd-dfa9134afa8d parameters, read in 7adaac85-b820-482f-8d7a-57011c19ad91:
{
  "ack_floor": {
    "consumer_seq": 0,
    "stream_seq": 0
  },
  "config": {
    "ack_wait": 30000000000,
    "deliver_group": "",
    "deliver_subject": "_INBOX.Lf0LN0Z8lf3x5p6xDdMx5I",
    "filter_subject": "",
    "max_ack_pending": 1,
    "max_deliver": -1,
    "max_waiting": 0,
    "notes": ""
  },
  "created": "2022-08-20T22:51:33.117390893Z",
  "delivered": {
    "consumer_seq": 0,
    "stream_seq": 0
  },
  "name": "5dc371f4-0da8-40e7-baca-a85529e51a22",
  "num_ack_pending": 0,
  "num_pending": 0,
  "num_redelivered": 0,
  "num_waiting": 0,
  "stream_name": "ba59220f-58fc-4f33-a7fd-dfa9134afa8d"
}
[2022-08-20 15:51:33,122: INFO manage_consumer.py:71 (13129) httpmq-sdk] Deleted stream ba59220f-58fc-4f33-a7fd-dfa9134afa8d with request 9bcded7b-58da-4d92-80a8-16ab48c3e986
```
