import ssl
import socket
from pathlib import Path
import selectors
from gui.types import BaseClient, BaseModel
from gui.model import Model
from logic.geometry import deserialize_rect
from server.spacial_store import SpacialStore
from typing import override
import threading
from communication.protocol import ServerMessageType, ClientMessageType, parse_server_msg, encode_msg
from logic.geometry import deserialize_rect
from gui.enums import LocationKind, AnswerKind
import os
import json

class Client(BaseClient):
    def __init__(self):
        self.protocol = None
        self.sel = selectors.DefaultSelector()
        self._model = None

    # ==== START methods from BaseClient ====
    @override
    def connect(self, addr, cert_path, connected: threading.Event, end: threading.Event, modelfactory: type[Model]=Model):
        """
        `connected` is set if the model is initialized and a connection
        has been established.
        `end` is set if the connection has ended.
        `end` can be set by the caller to end the connection.
        If the client failed to start a connection, `connection` and `end`
        are both set.
        """
        self._model = modelfactory(self)
        closed = threading.Event()
        self.protocol = ClientProtocol(self._model, closed)
        context = ssl.create_default_context()
        context.load_verify_locations(cert_path)
        try:
            with socket.create_connection(addr) as sock:
                with context.wrap_socket(sock, server_hostname=addr[0]) as xsock:
                    connected.set()
                    xsock.setblocking(False)
                    print(xsock.getsockname())
                    self.sel.register(xsock, selectors.EVENT_READ, self.protocol.data_received)
                    self.protocol.connection_made(xsock)
                    try:
                        while not end.is_set():
                            events = self.sel.select(0.2)
                            if end.is_set():
                                break
                            for key, mask in events:
                                callback = key.data
                                assert key.fileobj == xsock
                                assert callback == self.protocol.data_received
                                assert mask == selectors.EVENT_READ
                                try:
                                    data = xsock.recv(1024)
                                    if len(data) == 1024:
                                        print("warning: received package might be too large")
                                except ssl.SSLWantReadError:
                                    print("wanted to read but couldn't :(")
                                    continue
                                except ConnectionResetError as e:
                                    self.protocol.connection_lost(e)
                                    data = b""
                                else:
                                    if not data:
                                        print("Data Ended. Closing connection")
                                        self.protocol.eof_received()
                                if not data or end.is_set():
                                    break
                                self.protocol.data_received(data)
                    except KeyboardInterrupt:
                        print("Bye!")
                    finally:
                        self._terminate(xsock, end)
        except ConnectionRefusedError:
            print("connection refused")
            end.set()
        except Exception as e:
            end.set()
            raise e
        finally:
            connected.set()

    def _terminate(self, socket, end):
        self.sel.unregister(socket)
        socket.close()
        end.set()

    @override
    def handle_location(self, location: LocationKind):
        assert isinstance(location, LocationKind)
        match location:
            case LocationKind.SIGNUP | LocationKind.LOGIN:
                assert self._model is not None
                self._model.update_location(location)
            case x:
                print(f"TODO implement handle_location case {x}")
    
    @override
    def handle_gps(self, gps):
        print("needs to be implemented")
        # what is gps? needs to become a path: list[int]
        # path = ...
        # self.protocol.send(encode_msg(ClientMessageType.UPDATE_USER_AREA, [path]))

    @override
    def handle_login(self, username, password):
        assert self.protocol is not None
        self.protocol.send(encode_msg(ClientMessageType.LOGIN, [username, password]))

    @override
    def handle_signup(self, username, password):
        assert self.protocol is not None
        self.protocol.send(encode_msg(ClientMessageType.SIGNUP, [username, password]))

    @override
    def handle_others_accuracy(self, friend, depth_level):
        assert self.protocol is not None
        self.protocol.send(encode_msg(ClientMessageType.UPDATE_FRIEND_ACCURACY, [friend, str(depth_level)]))

    @override
    def handle_add_friend(self, friend: str):
        assert self.protocol is not None
        self.protocol.send(encode_msg(ClientMessageType.FRIEND_REQUEST, [friend]))

    @override
    def handle_remove_friend(self, friend: str):
        assert self.protocol is not None
        self.protocol.send(encode_msg(ClientMessageType.FRIEND_REMOVE, [friend]))
        self._model.delete_others(friend)
        self._model.remove_friend(friend)
        self._model.update_map()

    @override
    def handle_accept_request(self, friend: str, answer: AnswerKind):
        assert self.protocol is not None
        self.protocol.send(encode_msg(ClientMessageType.FRIEND_REQUEST_ANSWER, [friend, answer]))

        if answer == AnswerKind.ACCEPT:
            self._model.add_friend(friend)
            self._model.insert_others(friend)
            self._model.update_map()
    
    @override
    def handle_ready(self):
        self.protocol.bridge_ready.set()

    def start_gui(self):
        assert self._model is not None
        self._model.start_gui()


class ClientProtocol:
    def __init__(self, model: Model, closed: threading.Event):
        self.model = model
        self.closed = closed
        self.bridge_ready = threading.Event()
        self.s_store: SpacialStore | None = None

    # ==== START methods from asyncio.Protocol ====
    def connection_made(self, transport: socket.socket):
        print("connection made!")
        self.transport = transport

    def connection_lost(self, exc):
        if exc is None:
            print("connection lost: EOF Reached or closed by this side")
        else:
            print(f"connection lost because of exception: {exc}")
        self.closed.set()

    def data_received(self, data: bytes):
        # TODO parse data so that arbitrary splits in the stream are handled correctly
        print("received: ", data)
        unparsed_msg = data
        (msg_type, msg), err = parse_server_msg(unparsed_msg)
        if err:
            print(f"parsing of message {unparsed_msg} failed: {err}")
            return
        match msg_type:
            case ServerMessageType.LOGIN_SUCCESSFUL | ServerMessageType.SIGNUP_SUCCESSFUL:
                username, spacial_kind, spacial_rect = msg
                startrect = deserialize_rect(spacial_rect)
                self.s_store = SpacialStore(startrect)
                accuracies = self.s_store.get_accuracy_per_depth(20)

                if msg_type == ServerMessageType.LOGIN_SUCCESSFUL:
                    print(f"successfully logged in!")
                else:
                    print(f"successfully signed up!")

                self.model.set_user(username)
                self.model.update_location(LocationKind.MAIN)
                # (alex) client needs to wait until pywebview bridge is ready
                self.bridge_ready.wait()
                self.model.update_spacial(accuracies)
            case ServerMessageType.LOGIN_FAILED:
                print(f"login failed.. reason: {msg}")
            case ServerMessageType.SIGNUP_FAILED:
                print(f"login failed.. reason: {msg}")
            case ServerMessageType.UPDATE_USER_AREA:
                # Maybe ts can be used to get the rect from the path
                # Path is not being sent yet
                """ if msg[0] not in self.s_store.get_all_usernames():
                    self.s_store.insert(msg[0], int(msg[1]))

                rect = self.s_store.get_area(msg[0], msg[1]) """
                path = json.loads(msg[1])
                if not isinstance(path, list):
                    return
                if self.s_store is None:
                    print("s_store not initialized")
                    return
                r = self.s_store.path_to_rect(path)
                if r is None:
                    print(f"invalid path from server: {path}")
                    return
                self.model.update_user_rect(msg[0], r)
                self.model.update_map()
            # TODO update these cases to use the new enum values
            case ServerMessageType.FRIEND_REQUEST:
                self.model.request_received(msg[0])
            case ServerMessageType.FRIEND_REQUEST_ANSWER:
                # This is unnessecary becuase we have SET_FRIEND_ACCURACY.
                # If a request gets rejected we dont handle it anyways.
                """ if msg[1] == AnswerKind.ACCEPT:
                    self.model.add_friend(msg[0]) """
            case ServerMessageType.FRIEND_REMOVE:
                self.model.remove_friend(msg[0])
            case ServerMessageType.SET_FRIEND_ACCURACY:
                self.model.add_friend(msg[0], msg[1])
            case x:
                print(f"TODO Message type {x} not handled yet")

    def eof_received(self):
        print("connection lost: other side closed connection")
        self.closed.set()
    # ==== END methods from asyncio.Protocol ====

    def send(self, msg: bytes):
        # TODO add length of package before sending it
        sent = self.transport.send(msg)
        if sent == 0:
            raise RuntimeError("socket connection broken")

def main():
    c = Client()
    print(f"PID: {os.getpid()}")

    user = ["alex", [47.3745, 8.5445], 200]
    others = {
            "pascal" : ([47.373, 8.545], 300),
            "max" : ([47.379, 8.54], 100)
        }

    connected = threading.Event()
    end = threading.Event()
    def run_client():
        nonlocal connected, end, c
        c.connect(("localhost", 8443), Path("keys")/"localhost.crt", connected, end, Model)
    t = threading.Thread(target=run_client, name="client", args=())
    t.start()
    connected.wait()
    # TODO this is a bit obtrusive..
    if end.is_set():
        t.join()
        return
    c.start_gui()
    end.set()
    print(threading.enumerate())
    t.join()
