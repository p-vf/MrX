from collections.abc import Callable
import ssl
import selectors

class StateHandler:
    def handle(self, data: bytes, reply_callback: Callable[[bytes], None]):
        raise NotImplementedError("StateHandler.handle")

    def end(self):
        raise NotImplementedError("StateHandler.handle")

class Connection:
    def __init__(self, statehandler: StateHandler, selector: selectors.BaseSelector):
        self.statehandler = statehandler
        self.data_buffer= b""
        self.size_buffer = b""
        self.sel = selector
        pass

    def read(self, conn: ssl.SSLSocket, _):
        assert isinstance(conn, ssl.SSLSocket)
        while True:
            try:
                data = conn.recv(15)
            except ssl.SSLWantReadError:
                break
            if not data:
                self.statehandler.end()
                self.sel.unregister(conn)
                conn.close()
                break
            while True:
                len_size_buffer = len(self.size_buffer)
                if len_size_buffer < 8:
                    bytes_needed = 8 - len_size_buffer
                    self.size_buffer += data[:bytes_needed]
                    self.data_buffer = b""
                    data = data[bytes_needed:]
                    len_size_buffer = len(self.size_buffer)
                if len(self.size_buffer) < 8:
                    break
                expected_bytes = decode_number(self.size_buffer)
                print("expected length of package:", expected_bytes)
                assert expected_bytes >= 0, "length of size_buffer not enough"
                missing_bytes = expected_bytes - len(self.data_buffer)
                if len(data) >= missing_bytes:
                    self.statehandler.handle(self.data_buffer + data[:missing_bytes], lambda x: self.write(conn, x))
                    self.data_buffer = b""
                    self.size_buffer = b""
                    data = data[missing_bytes:]
                else:
                    self.data_buffer += data
                    break

    def write(self, sock: ssl.SSLSocket, data):
        data_to_send = int.to_bytes(len(data), 8) + data
        total_sent = 0
        while total_sent < len(data_to_send):
            sent = sock.send(data_to_send[total_sent:])
            if sent == 0:
                raise RuntimeError("socket connection broken")
            total_sent += sent

def decode_number(buf: bytes):
    if len(buf) >= 8:
        return int.from_bytes(buf[:8])
    return -1
