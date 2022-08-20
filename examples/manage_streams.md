# Manage Streams

Basic example showing how to manage streams with the client.

```shell
$ ./examples/manage_streams.py
[2022-08-20 15:21:28,361: INFO manage_streams.py:33 (11561) httpmq-sdk] Management API ready
[2022-08-20 15:21:28,363: INFO manage_streams.py:45 (11561) httpmq-sdk] Create stream 089c1d1e-64f5-417a-8afc-17b7ce627502 with request eb157a20-e2c9-4745-b6d4-bca24591211a
[2022-08-20 15:21:28,364: INFO manage_streams.py:51 (11561) httpmq-sdk] Stream 089c1d1e-64f5-417a-8afc-17b7ce627502 parameters, read in 6e4b0611-bc4f-4d8f-890c-a9012dd20291:
{
  "config": {
    "description": "",
    "max_age": 60000000000,
    "max_bytes": -1,
    "max_consumers": -1,
    "max_msg_size": -1,
    "max_msgs": -1,
    "max_msgs_per_subject": -1,
    "name": "089c1d1e-64f5-417a-8afc-17b7ce627502",
    "subjects": [
      "subj.1",
      "subj.2"
    ]
  },
  "created": "2022-08-20T22:21:28.362545345Z",
  "state": {
    "bytes": 0,
    "consumer_count": 0,
    "first_seq": 0,
    "first_ts": "0001-01-01T00:00:00Z",
    "last_seq": 0,
    "last_ts": "0001-01-01T00:00:00Z",
    "messages": 0
  }
}
[2022-08-20 15:21:28,367: INFO manage_streams.py:64 (11561) httpmq-sdk] Changed stream 089c1d1e-64f5-417a-8afc-17b7ce627502's target subjects with request aa866860-f3fe-46d7-8dd5-f049c62ebabb
[2022-08-20 15:21:28,368: INFO manage_streams.py:72 (11561) httpmq-sdk] Stream 089c1d1e-64f5-417a-8afc-17b7ce627502 parameters, read in 1bf4ef59-61dc-4568-9d56-2ddafd6aaba9:
{
  "config": {
    "description": "",
    "max_age": 60000000000,
    "max_bytes": -1,
    "max_consumers": -1,
    "max_msg_size": -1,
    "max_msgs": -1,
    "max_msgs_per_subject": -1,
    "name": "089c1d1e-64f5-417a-8afc-17b7ce627502",
    "subjects": [
      "subj.2",
      "subj.3"
    ]
  },
  "created": "2022-08-20T22:21:28.362545345Z",
  "state": {
    "bytes": 0,
    "consumer_count": 0,
    "first_seq": 0,
    "first_ts": "0001-01-01T00:00:00Z",
    "last_seq": 0,
    "last_ts": "0001-01-01T00:00:00Z",
    "messages": 0
  }
}
[2022-08-20 15:21:28,369: INFO manage_streams.py:87 (11561) httpmq-sdk] Changed stream 089c1d1e-64f5-417a-8afc-17b7ce627502's data retention with request d0a068cb-a17a-43c3-883e-43822c4fb998
[2022-08-20 15:21:28,371: INFO manage_streams.py:95 (11561) httpmq-sdk] Stream 089c1d1e-64f5-417a-8afc-17b7ce627502 parameters, read in 96ef84a2-81ed-4314-acbf-47473a715941:
{
  "config": {
    "description": "",
    "max_age": 900000000000,
    "max_bytes": -1,
    "max_consumers": -1,
    "max_msg_size": -1,
    "max_msgs": -1,
    "max_msgs_per_subject": -1,
    "name": "089c1d1e-64f5-417a-8afc-17b7ce627502",
    "subjects": [
      "subj.2",
      "subj.3"
    ]
  },
  "created": "2022-08-20T22:21:28.362545345Z",
  "state": {
    "bytes": 0,
    "consumer_count": 0,
    "first_seq": 0,
    "first_ts": "0001-01-01T00:00:00Z",
    "last_seq": 0,
    "last_ts": "0001-01-01T00:00:00Z",
    "messages": 0
  }
}
[2022-08-20 15:21:28,372: INFO manage_streams.py:106 (11561) httpmq-sdk] Deleted stream 089c1d1e-64f5-417a-8afc-17b7ce627502 with request 452d2a13-acf6-46ab-b230-61021e4db175
```
