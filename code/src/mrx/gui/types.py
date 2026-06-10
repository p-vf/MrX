from abc import abstractmethod
from pathlib import Path
from gui.enums import LocationKind
import threading
from logic.geometry import Rect

class UserData:
    def __init__(self, name: str, area: Rect, accuracy: float):
        self.name = name
        self.area = area
        self.accuracy = accuracy

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
    def update_location(self, location: LocationKind):
        pass

    @abstractmethod
    def update_user_rect(self, username: str, area: Rect):
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
    
    @abstractmethod
    def add_friend(self, friend):
        pass

    @abstractmethod
    def remove_friend(self, friend):
        pass

    @abstractmethod
    def request_recieved(self, friend):
        pass

    @abstractmethod
    def update_spacial(self, min_area, max_area):
        pass

    @abstractmethod
    def init_friendlist(self):
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
    def handle_others_accuracy(self, friend, depth_level):
        pass

    @abstractmethod
    def handle_accuracy(self, depth_level):
        pass

    @abstractmethod
    def handle_init_map(self):
        pass

    @abstractmethod
    def handle_add_friend(self, friend):
        pass
    
    @abstractmethod
    def handle_remove_friend(self, friend):
        pass

    @abstractmethod
    def handle_accept_request(self, friend, answer):
        pass

