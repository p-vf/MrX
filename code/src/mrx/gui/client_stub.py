from communication.keygen import get_cert
from typing import override

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
        self.model.update_location(location.value)

    @override
    def handle_login(self, username, password):
        print("handling login")
        self.model.update_user(username=username)

    @override
    def handle_signup(self, username, password):
        print("handling signup")
        self.model.update_user(username=username)
        self.model.update_location(2)

    @override
    def handle_accuracy(self, accuracy):
        print("handling accuracy")
        self.model.update_user(accuracy=accuracy)
        self.model.update_map()

    @override
    def handle_init_map(self):
        print("handling initialization of map")
        self.model.update_map()


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
        print("running run_client")
        c.connect(("localhost", 8443), Path("keys")/"localhost.crt", connected, end, Model)
    t = threading.Thread(target=run_client, name="client", args=())
    t.start()
    connected.wait()
    c.start_gui()
    end.set()
    print(threading.enumerate())
    t.join()
