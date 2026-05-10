from pathlib import Path
from collections.abc import Callable
import ssl
import socket
import os
import selectors
from .common import StateHandler, Connection

from .keygen import generate_key, get_or_generate_cert

def main() -> None:
    print(f"PID: {os.getpid()}")
    # use socket.gethostname() instead of "localhost" if used for real
    s = Server("localhost", 8443, Path("keys"))
    s.start()

class Server:
    def __init__(self, hostname: str, port: int, keydir: Path):
        self.addr = (hostname, port)
        self.keydir = keydir
        self.sel = selectors.DefaultSelector()
        pass

    def start(self):
        cert = get_or_generate_cert(self.keydir)
        print(cert)
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(self.keydir/"localhost.pem", self.keydir/"localhost.key")
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0) as sock:
            sock.bind(self.addr)
            sock.listen(5)
            sock.setblocking(False)
            with context.wrap_socket(sock, server_side=True) as ssock:
                self.sel.register(ssock, selectors.EVENT_READ, self.accept)
                while True:
                    events = self.sel.select(0.1)
                    for key, mask in events:
                        callback = key.data
                        callback(key.fileobj, mask)

    def accept(self, sock, mask):
        conn, addr = sock.accept()
        print("new connection with address:", addr)
        conn.setblocking(False)
        handler = EchoStateHandler()
        connection = Connection(handler, self.sel)
        self.sel.register(conn, selectors.EVENT_READ, connection.read)

    # def read(self, conn: ssl.SSLSocket, mask):
    #     assert isinstance(conn, ssl.SSLSocket)
    #     data = conn.recv(1000)
    #     if data:
    #         print("echoing", repr(data), "to", conn)
    #         conn.send(data)
    #     else:
    #         print("closing", conn)
    #         self.sel.unregister(conn)
    #         conn.close()


# simple echo behaviour
class EchoStateHandler(StateHandler):
    def __init__(self):
        self.log: list[bytes] = []

    def handle(self, data: bytes, reply_callback: Callable[[bytes], None]):
        print("received", data)
        self.log.append(data)
        reply_callback(data)

    def end(self):
        print("log of messages received:", self.log)
