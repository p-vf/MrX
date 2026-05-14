# Just placeholder, can be changed later

import json

def encode_message(msg: dict) -> bytes:
    return json.dumps(msg).encode()

def decode_message(data: bytes) -> dict:
    return json.loads(data.decode())