from abc import abstractmethod
from pathlib import Path
from gui.enums import LocationKind
import threading

class BaseModel:
    @abstractmethod
    def __init__(self, client):
        pass

    @abstractmethod
    def get_user(self) -> list:
        pass

    @abstractmethod
    def get_others(self) -> dict:
        pass

    @abstractmethod
    def set_user(self, user):
        pass

    @abstractmethod
    def set_others(self, others):
        pass

    @abstractmethod
    def update_location(self, location):
        pass

    @abstractmethod
    def update_user(self, username=None, position=None, accuracy=None):
        pass

    @abstractmethod
    def insert_others(self, username, position, accuracy):
        pass

    @abstractmethod
    def delete_others(self, username):
        pass

    @abstractmethod
    def update_others(self, old_un, new_un=None, position=None, accuracy=None):
        pass

    @abstractmethod
    def update_map(self):
        pass

    @abstractmethod
    def start_gui(self):
        pass

# interfaces for mocking and stuff
class BaseClient:
    @abstractmethod
    def __init__(self):
        pass

    @abstractmethod
    def connect(self, addr: tuple[str, int], cert_path: Path, connected: threading.Event, end: threading.Event, modelfactory: type[BaseModel]):
        pass

    @abstractmethod
    def handle_location(self, location: LocationKind):
        pass

    @abstractmethod
    def handle_login(self, username: str, password: str):
        pass

    @abstractmethod
    def handle_signup(self, username, password):
        pass

    @abstractmethod
    def handle_accuracy(self, accuracy):
        pass

    @abstractmethod
    def handle_init_map(self):
        pass
