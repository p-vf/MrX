from pathlib import Path
from collections.abc import Callable
import ssl
import socket
import os
import selectors
import asyncio
import json

from communication.protocol import ClientMessageType, ServerMessageType, parse_client_msg, encode_msg
from database.create_user_db import create_user_db
from database.user_db import UserDBManager
from server.spacial_store import SpacialStore
from server.permission_store import PermissionStore
from logic.geometry import serialize_rect, Rect

from communication.keygen import generate_key, get_or_generate_cert


def main() -> None:
    print(f"PID: {os.getpid()}")
    asyncio.run(start_server())
    # # use socket.gethostname() instead of "localhost" if used for real
    # host = "localhost"
    # port = 8443
    # print(f"listening on address ({host}, {port})")
    # s = ServerOld("localhost", 8443, Path("keys"))
    # s.start()

# example region: rect that bounds Switzerland
# TODO store these locations
spacialstore = SpacialStore(Rect(45.6283, 5.8722, 47.6283, 10.8722))
spacialstore.insert("chad", [2, 3, 3, 0, 0, 0])
spacialstore.insert("chud", [2, 3, 1, 0, 0, 0])

permissionstore = PermissionStore()
permissionstore.update("chad", "chud", 4)

online_users: dict[str, "Server"] = dict()

class Server(asyncio.Protocol):
    def __init__(self, db_manager: UserDBManager):
        self.peername = None
        self.username = None
        self.db_manager = db_manager
        self.spacial_db = spacialstore
        self.permissions_db = permissionstore

    # ==== START methods from asyncio.Protocol ====
    def connection_made(self, transport):
        assert isinstance(transport, asyncio.WriteTransport)
        self.peername = transport.get_extra_info("peername")
        print(f"connection from {self.peername}")
        self.transport = transport

    def connection_lost(self, exc):
        if self.username is not None:
            del online_users[self.username]
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
                username, password = msg
                login_successful = self.db_manager.is_valid_login(username, password)
                if login_successful:
                    # TODO the username should not have to be sent, the client
                    # should already know this information in principle
                    online_users[username] = self
                    self.username = username
                    self.send(encode_msg(ServerMessageType.LOGIN_SUCCESSFUL, [username]))
                    self.send_all_user_areas()
                    return
                if self.db_manager.get_user(username) is None:
                    self.send(encode_msg(ServerMessageType.LOGIN_FAILED, ["user not in database"]))
                    return
                self.send(encode_msg(ServerMessageType.LOGIN_FAILED, ["wrong password"]))
                # TODO change the state of this connection (user is now logged in)
            case ClientMessageType.SIGNUP:
                username, password = msg
                assert isinstance(username, str)
                assert isinstance(password, str)
                if self.db_manager.get_user(username) is not None:
                    print(f"user {msg[0]} already in database")
                    self.send(encode_msg(ServerMessageType.SIGNUP_FAILED, ["username already taken"]))
                    return
                err = self.db_manager.insert_user(username, 0, password)
                if err:
                    self.send(encode_msg(ServerMessageType.SIGNUP_FAILED, ["db error"]))
                    print(f"db error: {err}")
                    return
                self.send(encode_msg(ServerMessageType.SIGNUP_SUCCESSFUL, []))
                self.send_all_user_areas()
                # TODO change the state of this connection (user is now logged in or smthn)
            case x:
                print(f"Message type {x} not handled yet")

    def send_all_user_areas(self):
        assert self.username is not None
        users = self.spacial_db.get_all_users()
        for user in users:
            perms = self.permissions_db.get_perm_for_user(self.username)
            if user in perms:
                acc = perms[user]
                self.send(encode_msg(ServerMessageType.UPDATE_USERAREA, [user, serialize_rect(self.spacial_db.get_area(user, acc))]))

    def eof_received(self):
        print("other party closed connection")
    # ==== END methods from asyncio.Protocol ====

    def send(self, msg: bytes):
        # TODO add length of package to it before sending it
        print(f"sending {msg}")
        self.transport.write(msg)

userdatabase_path = Path("serverdata") / "users.db"
async def start_server():
    os.makedirs(userdatabase_path.parent, exist_ok = True)
    create_user_db(userdatabase_path)
    manager = UserDBManager(userdatabase_path)
    print("created user database")
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
        lambda: Server(manager),
        'localhost', 8443
        , ssl=context
        )

    async with server:
        await server.serve_forever()

