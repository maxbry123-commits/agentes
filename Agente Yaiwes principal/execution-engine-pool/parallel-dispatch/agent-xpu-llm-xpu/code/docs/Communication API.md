# Usage
First connect through the socket(UDS socket specified by path)

# Client Request API
## Infer
Parameters:
- `type`: int - Type of request, must be 0 for infer
- `prompt`: list[int] - The input sequence of integers to be processed
- `priority`: int - Priority level for the request (0 is highest, for reactive requests)

> **Warning**: Only one infer request can be processed at a time.

Example:
```json
{
    "type": 0,
    "prompt": [1, 2, 3, 4, 5],
    "priority": 0
}
```

# Server Response API
> Every Response message Ends with a newline character.
## Info Message
Parameters:
- `type`: int - Type of message, must be 0 for info
- `subtype`: int - Subtype of message, you can get the subtype from the following list
- `message`: str - The information message to be displayed

Example:
```json
{
    "type": 0,
    "subtype": 0,
    "message": "Accept Infer Request"
}
```

### List of Info Messages
0. 
- `Accept Infer Request`: Indicates that the infer request has been accepted.
1. 
- `Infer Request Not Accepted because of there is already one infer request`: Indicates that the infer request was not accepted because there is already one infer request being processed.
- `Infer Request Not Accepted because of unknown error`: Indicates that the infer request was not accepted due to an unknown error.
2. `Infer Request Completed`: Indicates that the infer request has been completed. No further infer results will be sent. The server can accept new infer requests.


## Infer Result
Parameters:
- `type`: int - Type of message, must be 1 for infer Result
- `result`: int - The result of the inference

Example:
```json
{
    "type": 1,
    "result": 1
}
```

>**Note**: Usually, the result contains only one token.