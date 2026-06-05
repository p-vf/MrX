from collections.abc import Callable
import ssl
import selectors


def decode_number(buf: bytes):
    if len(buf) >= 8:
        return int.from_bytes(buf[:8])
    return -1
