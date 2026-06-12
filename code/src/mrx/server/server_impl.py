from pathlib import Path
from collections.abc import Callable
import ssl
import socket
import os
import selectors
import asyncio
import json
from datetime import datetime, timedelta

from communication.protocol import ClientMessageType, ServerMessageType, parse_client_msg, encode_msg
from database.create_user_db import create_user_db
from database.user_db import UserDBManager
from server.spacial_store import SpacialStore
from server.permission_db import PermissionDBManager, create_perm_db, PermissionStore
from server.pending_request_db import PendingRequestDBManager, create_pending_request_db
from logic.geometry import serialize_rect, Rect
from collections import deque
import pprint

from communication.keygen import get_or_generate_cert

LOGIN_FAIL_TIMEOUT_SEC = 10
MESSAGE_TIME_WINDOW_SIZE = 20
MAX_MESSAGES_PER_SEC = 15

def main() -> None:
    print(f"PID: {os.getpid()}")
    try:
        asyncio.run(start_server())
    except KeyboardInterrupt:
        print("Bye!")
    # # use socket.gethostname() instead of "localhost" if used for real
    # host = "localhost"
    # port = 8443
    # print(f"listening on address ({host}, {port})")
    # s = ServerOld("localhost", 8443, Path("keys"))
    # s.start()

online_users: dict[str, "Server"] = dict()

class Server(asyncio.Protocol):
    def __init__(self, db_manager: UserDBManager, spacialstore: SpacialStore, permissionstore: PermissionStore):
        self.peername = None
        self.username = None
        self.db_manager = db_manager
        self.spacial_db = spacialstore
        self.permissions_db = permissionstore
        self.pending_requests = set()
        self.last_login_attempt: datetime | None = None
        self.last_message_times: deque[datetime] = deque()

    # ==== START methods from asyncio.Protocol ====
    def connection_made(self, transport):
        assert isinstance(transport, asyncio.WriteTransport)
        self.peername = transport.get_extra_info("peername")
        print(f"connection from {self.peername}")
        self.transport = transport

    def connection_lost(self, exc):
        if self.username is not None:
            self.remove_self_online_users()
        if exc is None:
            print("connection closed because of EOF being reached or because this side closed it")
        else:
            print("connection closed by exception:", exc)

    def data_received(self, data: bytes):
        # TODO parse data correctly so that arbitrary splits in the stream are handled
        # print(f"received: {data} from {self.peername}")
        self.update_message_times()
        unparsed_msg = data
        (msg_type, msg), err = parse_client_msg(unparsed_msg)
        if err:
            print(f"parsing of message {unparsed_msg} failed: {err}")
            return
        match msg_type:
            case ClientMessageType.LOGIN:
                if self.last_login_attempt is not None:
                    d = datetime.now() - self.last_login_attempt
                    if d.total_seconds() < LOGIN_FAIL_TIMEOUT_SEC:
                        print(f"LOGIN refused: connection is timed out: {LOGIN_FAIL_TIMEOUT_SEC - d.total_seconds():.2}s remaining")
                        self.send(encode_msg(ServerMessageType.LOGIN_FAILED, [f"login timeout: {LOGIN_FAIL_TIMEOUT_SEC - d.total_seconds():.2}s remaining"]))
                        # TODO we could end the connection here or log this event
                        return
                username, password = msg
                login_successful = self.db_manager.is_valid_login(username, password)
                if login_successful:
                    # TODO the username should not have to be sent, the client
                    # should already know this information in principle
                    if username not in online_users:
                        online_users[username] = self
                    else:
                        self.send(encode_msg(ServerMessageType.LOGIN_FAILED, [f"user already online. Must wait {LOGIN_FAIL_TIMEOUT_SEC} seconds until next login attempt"]))
                        self.last_login_attempt = datetime.now()
                        return
                    self.username = username
                    print(f"user {username} logged in")
                    print(f"{online_users = }")
                    self.send(encode_msg(ServerMessageType.LOGIN_SUCCESSFUL, [username, str(1), serialize_rect(self.spacial_db.startrect)]))
                    self.send_all_user_areas_and_accuracies()
                    return
                if self.db_manager.get_user(username) is None:
                    self.send(encode_msg(ServerMessageType.LOGIN_FAILED, [f"user not in database. Must wait {LOGIN_FAIL_TIMEOUT_SEC} seconds until next login attempt"]))
                    self.last_login_attempt = datetime.now()
                    return
                self.send(encode_msg(ServerMessageType.LOGIN_FAILED, [f"wrong password. Must wait {LOGIN_FAIL_TIMEOUT_SEC} seconds until next login attempt"]))
                self.last_login_attempt = datetime.now()
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
                self.username = username
                online_users[username] = self
                self.send(encode_msg(ServerMessageType.SIGNUP_SUCCESSFUL, [username, str(1), serialize_rect(self.spacial_db.startrect)]))
                self.send_all_user_areas_and_accuracies()
                # TODO change the state of this connection (user is now logged in or smthn)
            case ClientMessageType.UPDATE_FRIEND_ACCURACY:
                assert self.username is not None
                user, depth_str = msg
                depth = int(depth_str)
                self.permissions_db.update(user, self.username, depth)
                if user in online_users:
                    online_users[user].send_user_area(self.username)
            case ClientMessageType.FRIEND_REQUEST:
                assert self.username is not None
                if len(msg) != 1:
                    print("WARNING: Friend request not sent correctly: expected one message member")
                    return
                user, = msg
                # TODO maybe we have to store these somewhere?
                if user in online_users:
                    online_users[user].send(encode_msg(ServerMessageType.FRIEND_REQUEST, [self.username]))
                    online_users[user].pending_requests.add(self.username)
                else:
                    # TODO:
                    print("TODO handle friend requests to users that are offline")
            case ClientMessageType.FRIEND_REQUEST_ANSWER:
                assert self.username is not None
                user, accept = msg
                if user not in self.pending_requests:
                    print("WARNING: malicious client: responded to request that never existed.")
                    return
                self.pending_requests.remove(user)
                if accept == "1":
                    self.permissions_db.update(self.username, user, 0)
                    self.permissions_db.update(user, self.username, 0)
                    self.send_user_area(user)
                    self.send_user_accuracy(user)
                    if user in online_users:
                        online_users[user].send_user_area(self.username)
                        online_users[user].send_user_accuracy(self.username)
            case ClientMessageType.FRIEND_REMOVE:
                assert self.username is not None
                user, = msg
                self.permissions_db.update(self.username, user, -1)
                self.permissions_db.update(user, self.username, -1)
                if user in online_users:
                    online_users[user].send(encode_msg(ServerMessageType.FRIEND_REMOVE, [self.username]))
            case ClientMessageType.UPDATE_USER_AREA:
                assert self.username is not None
                path_json, = msg
                path = json.loads(path_json)
                self.spacial_db.insert(self.username, path)
                for user in online_users:
                    if self.username in self.permissions_db.get_perm_for_user(user):
                        online_users[user].send_user_area(self.username)
                #print("TODO handle UPDATE_AREA")
            case x:
                print(f"Message type {x} not handled yet")

    def update_message_times(self):
        self.last_message_times.append(datetime.now())
        if len(self.last_message_times) > MESSAGE_TIME_WINDOW_SIZE:
            self.last_message_times.popleft()
            start = self.last_message_times[0]
            end = self.last_message_times[-1]
            td = (end-start).total_seconds()
            messages_per_sec = MESSAGE_TIME_WINDOW_SIZE / td
            if messages_per_sec > MAX_MESSAGES_PER_SEC :
                print(f"WARNING: user {self.username} has exceeded maximal messages per second ({MAX_MESSAGES_PER_SEC}): sent {MESSAGE_TIME_WINDOW_SIZE} messages in {td:.2} seconds")

    def send_user_area(self, user):
        """send the area of `user` to the client that is connected to `self`.
        should only be called if the `self` has permissions to get the area of `user`."""
        assert self.username is not None
        perms = self.permissions_db.get_perm_for_user(self.username)
        if user == self.username:
            # send the user's location to the full precision
            self.send(encode_msg(ServerMessageType.UPDATE_USER_AREA, [user, json.dumps(self.spacial_db.get_path(user))]))
        elif user in perms:
            acc = perms[user]
            if self.spacial_db.has_user(user):
                self.send(encode_msg(ServerMessageType.UPDATE_USER_AREA, [user, json.dumps(self.spacial_db.get_path(user)[:acc])]))
        else:
            print(f"WARNING: tried to send region of user {user} to {self.username} but permissions don't allow")
            print(f"PERMISSIONS: {perms}")

    def send_user_accuracy(self, user):
        """send the accuracy that `self` has given to `user`."""
        assert self.username is not None
        perm_settings = self.permissions_db.get_perm_settings_of_user(self.username)
        if user in perm_settings:
            self.send(encode_msg(ServerMessageType.SET_FRIEND_ACCURACY, [user, str(perm_settings[user])]))
        else:
            print(f"WARNING: trying to send settings for user {user} even though{self.username} has not set the accuracy for them. (probably because of assymmetric friends relation)")

    def send_all_user_areas_and_accuracies(self):
        assert self.username is not None
        perms = self.permissions_db.get_perm_for_user(self.username)
        for user in perms:
            self.send_user_area(user)
            self.send_user_accuracy(user)

    def eof_received(self):
        if self.username is not None:
            self.remove_self_online_users()
        print("other party closed connection")
    # ==== END methods from asyncio.Protocol ====

    def send(self, msg: bytes):
        # TODO add length of package to it before sending it
        self.transport.write(msg)

    def remove_self_online_users(self):
        """cleans up online_users after a connection loss. should only be called if `self.username` is not None."""
        if self.username in online_users:
            del online_users[self.username]
            self.spacial_db.remove_user(self.username)
        else:
            print(f"WARNING: remove_self_online_users: username {self.username} not in online_users")
            print(f"online_users: {online_users}")

userdatabase_path = Path("serverdata") / "users.db"
async def start_server():
    os.makedirs(userdatabase_path.parent, exist_ok = True)

    spacialstore = SpacialStore(Rect(45.6283, 5.8722, 47.6283, 10.8722))

    create_perm_db(userdatabase_path)
    permissionstore = PermissionDBManager(userdatabase_path)
    permissionstore.load_perms()

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
        lambda: Server(manager, spacialstore, permissionstore),
        'localhost', 8443
        , ssl=context
        )

    async with server:
        await server.serve_forever()

