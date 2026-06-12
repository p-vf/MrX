import enum
from typing import TypeVar
import base64

@enum.unique
class ServerMessageType(enum.Enum):
    LOGIN_SUCCESSFUL = 0
    LOGIN_FAILED = 1
    SIGNUP_SUCCESSFUL = 2
    SIGNUP_FAILED = 3
    UPDATE_USER_AREA = 4
    FRIEND_REQUEST = 5
    FRIEND_REQUEST_ANSWER = 6
    FRIEND_REMOVE = 7
    SET_FRIEND_ACCURACY = 8

@enum.unique
class ClientMessageType(enum.Enum):
    LOGIN = 0
    SIGNUP = 1
    UPDATE_FRIEND_ACCURACY = 2
    FRIEND_REQUEST = 3
    FRIEND_REQUEST_ANSWER = 4
    FRIEND_REMOVE = 5
    UPDATE_USER_AREA = 6

# TODO (p-vf) this could be made a bit more smart: instead of just encoding and
# decoding the data as list[str], we could encode and decode the data according
# to the message type. I.e. if we expect a UPDATE_USERAREA to have an area as data
# we could encode and then decode this data as such. This would also be useful
# for checking the type of the data.

def encode_msg(message_type: ServerMessageType | ClientMessageType, data: list[str]) -> bytes:
    # TODO instead of sending the enum name, we could send the number that identifies this enum
    return f"{message_type.name} {" ".join(list(map(lambda x: base64.b64encode(x.encode()).decode(), data)))}".encode()

T = TypeVar("T")
def parse_msg[T: enum.Enum](msg: bytes, enumtype: type[T]) -> tuple[tuple[T | None, list[str]], str]:
    if b" " not in msg:
        return (None, []), "invalid message: {msg}"
    msg_type, data = msg.split(b" ", 1)
    msg_type_parsed = None
    err = ""
    try:
        msg_type_parsed = enumtype[msg_type.decode()]
    except KeyError:
        err = f"invalid message: {msg}"
        return (None, []), err

    fields: list[str] = []
    if data != b"":
        for field in data.split(b" "):
            fields.append(base64.b64decode(field).decode())
    #print(f"received and parsed message: {msg_type_parsed}, {fields}")
    return (msg_type_parsed, fields), err

def parse_server_msg(msg: bytes) -> tuple[tuple[ServerMessageType | None, list[str]], str]:
    return parse_msg(msg, ServerMessageType)

def parse_client_msg(msg: bytes) -> tuple[tuple[ClientMessageType | None, list[str]], str]:
    return parse_msg(msg, ClientMessageType)