from communication.keygen import get_cert
from typing import override
from gui.enums import AnswerKind, LocationKind
from logic.geometry import Rect
from server.spacial_store import SpacialStore

from .model import Model
from gui.types import BaseClient
from communication.client import Client
from pathlib import Path
import asyncio
import threading
import time
import os

class ClientStub(BaseClient):
    def __init__(self):
        self.model = Model(self)

    @override
    def connect(self, addr, cert_path, connected, end, modelfactory):
        self.cert = get_cert(cert_path)

    @override
    def handle_location(self, location):
        print("handling location change")
        self.model.update_location(location)

    @override
    def handle_login(self, username, password):
        print("handling login")
        self.model.set_user(username=username)
        self.model.update_location(LocationKind.MAIN)

        spacialstore = SpacialStore(Rect(45.6283, 5.8722, 47.6283, 10.8722))
        spacialstore.insert("chad", [2, 3, 3, 0,])
        spacialstore.insert("chud", [2, 0, 0, 0, 0])
        spacialstore.insert("sub5", [2, 3, 0, 0, 0, 0])

        users = spacialstore.get_all_users()
        for user in users:
            self.model.update_user_rect(user, users[user])

    @override
    def handle_signup(self, username, password):
        print("handling signup")
        self.model.set_user(username=username)
        self.model.update_location(LocationKind.MAIN)

    @override
    def handle_others_accuracy(self, friend, depth_level):
        print(f"handling {friend}s accuracy, setting it to: {depth_level}")

    @override
    def handle_init_map(self):
        print("handling initialization of map")
        self.model.update_map()
        self.model.update_spacial([4000, 1000, 250, 100])
        self.model.init_friendlist()
        self.model.request_received("ben")
        self.model.request_received("anderdingus")
    
    # client made friend request to "friend"
    # currently not adding "friend" : rect to 
    @override
    def handle_add_friend(self, friend):
        print(f"handling adding friend: {friend}")
        self.model.add_friend(friend)
        self.model.update_map()

    # client wants to remove friend "friend"
    @override
    def handle_remove_friend(self, friend):
        print(f"handling removing friend: {friend}")
        self.model.remove_friend(friend)
        self.model.update_map()

    @override
    def handle_request_received(self, friend):
        self.model.request_received(friend)
    
    # client wants to accept/reject the friend request from "friend"
    @override
    def handle_accept_request(self, friend, answer):
        print(f"handling accepting request: {friend}, {answer}")
        self.model.request_response(friend, answer)
            
    def start_gui(self):
        assert self.model is not None
        self.model.start_gui()

def main():
    c = ClientStub()
    print(f"PID: {os.getpid()}")

    user = ["alex", [47.3745, 8.5445], 200]
    others = {
            "pascal" : ([47.373, 8.545], 300),
            "max" : ([47.379, 8.54], 100)
        }

    """ connected = threading.Event()
    end = threading.Event()
    def run_client():
        nonlocal connected, end, c
        print("running run_client")
        c.connect(("localhost", 8443), Path("keys")/"localhost.crt", connected, end, Model)
    t = threading.Thread(target=run_client, name="client", args=())
    t.start()
    connected.wait()
    c.start_gui()
    end.set()
    print(threading.enumerate())
    t.join() """

    c.start_gui()
