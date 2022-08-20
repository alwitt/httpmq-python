# Sending and Receiving Messages

Basic example showing how to publish and subscribe for messages.

```shell
$ ./examples/sending_messages.py
[2022-08-20 16:47:42,249: INFO sending_messages.py:30 (17520) httpmq-sdk] Management API ready
[2022-08-20 16:47:42,251: INFO sending_messages.py:42 (17520) httpmq-sdk] Create stream fa616313-591a-4dc0-9dbf-8fafe0d9ffd5 with request bec667a2-04c8-42ed-880f-84cd38a324f2
[2022-08-20 16:47:42,253: INFO sending_messages.py:53 (17520) httpmq-sdk] Create consumer fdfba887-1713-412b-ac1b-06efae4bca41 with request d455d6ce-c61d-449c-b4c4-c91338b9abfb
[2022-08-20 16:47:42,254: INFO sending_messages.py:58 (17520) httpmq-sdk] Data plane API ready
[2022-08-20 16:47:42,256: INFO sending_messages.py:92 (17520) httpmq-sdk] Published message 'Hello world b2143492-3f44-4ad8-b715-c25528b9cb13' to 'subj.1' in request d624e5e6-654e-48ce-b7b9-03a0952db10e
[2022-08-20 16:47:42,509: INFO sending_messages.py:101 (17520) httpmq-sdk] Read: 'Hello world b2143492-3f44-4ad8-b715-c25528b9cb13'
[2022-08-20 16:47:42,511: INFO sending_messages.py:108 (17520) httpmq-sdk] ACKed message in request 1415b8fd-b094-455b-aabd-bc98266cbc26
[2022-08-20 16:47:42,762: INFO sending_messages.py:113 (17520) httpmq-sdk] Push-subscribe request ID 841645c0-ea8b-4a11-a5b4-d7cb713a1b3b
[2022-08-20 16:47:42,774: INFO sending_messages.py:119 (17520) httpmq-sdk] Deleted stream fa616313-591a-4dc0-9dbf-8fafe0d9ffd5 with request ba842b95-153a-47e7-a68a-a92135cb5d63
```
