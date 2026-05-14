import ssl
import socket
from pathlib import Path
from .common import Connection, StateHandler
import selectors

def main() -> None:
    print(f"hello from client, {"TLSv1_3 is available!" if ssl.HAS_TLSv1_3 else "TLSv1_3 not available :("}")
    c = Client("localhost", 8443, Path("keys")/"localhost.crt")
    c.start()

class Client:
    def __init__(self, hostname: str, port: int, certfile: Path):
        self.addr = (hostname, port)
        self.certfile = certfile
        self.state_handler = ClientStateHandler()
        self.sel = selectors.DefaultSelector()
        self.connection = Connection(self.state_handler, self.sel)

    def start(self):
        context = ssl.create_default_context()
        context.load_verify_locations(self.certfile)
        with socket.create_connection(self.addr) as sock:
            with context.wrap_socket(sock, server_hostname=self.addr[0]) as xsock:
                print(xsock.getsockname())
                self.sel.register(xsock, selectors.EVENT_READ, self.connection.read)
                self.state_handler.start(xsock, self.connection)
                try:
                    while True:
                        events = self.sel.select(0.1)
                        for key, mask in events:
                            callback = key.data
                            callback(key.fileobj, mask)
                except KeyboardInterrupt:
                    print("Bye!")

class ClientStateHandler(StateHandler):
    def __init__(self):
        pass

    def start(self, sock: ssl.SSLSocket, conn: Connection):
        data = input("> ").encode()
        conn.write(sock, data)

    def handle(self, data, reply_callback):
        print("<", data)
        reply = input("> ").encode()
        reply_callback(reply)

        # Implementation of the answer of the client could be structured like that
        # msg = {
        #     "vertical": vertical,
        #     "horizontal": horizontal,
        #     "continue": True
        # }

    def end(self):
        print("server closed connection")
