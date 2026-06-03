from pathlib import Path
from collections.abc import Callable
import ssl
import socket
import os
import selectors
from .common import StateHandler, Connection
import asyncio
from communication.protocol import ClientMessageType, ServerMessageType, parse_client_msg, encode_msg

from .keygen import generate_key, get_or_generate_cert
from ..logic.quadtree import QuadTreeNode, Rectangle


def main() -> None:
    print(f"PID: {os.getpid()}")
    asyncio.run(start_server())
    # # use socket.gethostname() instead of "localhost" if used for real
    # host = "localhost"
    # port = 8443
    # print(f"listening on address ({host}, {port})")
    # s = ServerOld("localhost", 8443, Path("keys"))
    # s.start()


class Server(asyncio.Protocol):
    def __init__(self):
        self.loop = asyncio.get_running_loop()
        self.peername = None

    # ==== START methods from asyncio.Protocol ====
    def connection_made(self, transport):
        assert isinstance(transport, asyncio.WriteTransport)
        self.peername = transport.get_extra_info("peername")
        print(f"connection from {self.peername}")
        self.transport = transport

    def connection_lost(self, exc):
        if exc is None:
            print("connection closed because of EOF being reached or because this side closed it")
        else:
            print("connection closed by exception:", exc)

    def data_received(self, data: bytes):
        # TODO parse data correctly so that arbitrary splits in the stream are handled
        print(f"received: {data} from {self.peername}")
        unparsed_msg = data
        (msg_type, msg), err = parse_client_msg(unparsed_msg)
        if err:
            print(f"parsing of message {unparsed_msg} failed: {err}")
            return
        match msg_type:
            case ClientMessageType.LOGIN:
                print(f"login attempt: {msg}")
                # TODO implement check with login database here
                login_successful = True
                if login_successful:
                    self.send(encode_msg(ServerMessageType.LOGIN_SUCCESSFUL, []))
                else:
                    self.send(encode_msg(ServerMessageType.LOGIN_FAILED, ["user not in database"]))
            case x:
                print(f"Message type {x} not handled yet")

    def eof_received(self):
        print("other party closed connection")
    # ==== END methods from asyncio.Protocol ====

    def send(self, msg: bytes):
        # TODO add length of package to it before sending it
        print(f"sending {msg}")
        self.transport.write(msg)

async def start_server():
    loop = asyncio.get_running_loop()

    keydir = Path("keys")
    cert = get_or_generate_cert(keydir)
    print(cert)
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    try:
        context.load_cert_chain(keydir/"localhost.crt", keydir/"localhost.key")
    except FileNotFoundError as e:
        print(f"files: {keydir/"localhost.crt"}, {keydir/"localhost.key"}")
        raise e

    server = await loop.create_server(
        Server,
        'localhost', 8443
        , ssl=context
        )

    async with server:
        await server.serve_forever()


class ServerOld:
    def __init__(self, hostname: str, port: int, keydir: Path):
        self.addr = (hostname, port)
        self.keydir = keydir
        self.sel = selectors.DefaultSelector()

        world = Rectangle(0, 0, 100, 100)
        self.quadtree = QuadTreeNode(world)
        pass

    def start(self):
        cert = get_or_generate_cert(self.keydir)
        print(cert)
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        try:
            context.load_cert_chain(self.keydir/"localhost.crt", self.keydir/"localhost.key")
        except FileNotFoundError as e:
            print(f"files: {self.keydir/"localhost.crt"}, {self.keydir/"localhost.key"}")
            raise e
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
        # handler = LocationStateHandler(self.quadtree)
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
