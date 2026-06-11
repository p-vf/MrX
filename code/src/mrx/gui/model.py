from .gui import Gui
from gui.types import BaseModel
from logic.geometry import Rect
from gui.enums import UpdateKind, AnswerKind, LocationKind, Change

class Model(BaseModel):
    def __init__(self, client):
        self.location: LocationKind = LocationKind.LOGIN  #location in the gui => login.html etc.
        self.username: str | None = None
        self.users: dict[str, Rect] = {} # area of the users friends
        self.area_steps: list[int] | None = None # this is for the slider so you can set the accuracy for ur friends
        # [4000m2, 1000m2, 250m2 ... 40m2]
 
        self.gui = Gui(client)
        self.updates = self.gui.get_update_queue()
    
    # Needs to be called once to start the gui
    def start_gui(self):
        self.gui.start()
    
    def set_user(self, username: str):
        self.username = username
    
    def set_users(self, users):
        self.users = users
    
    # update location in the gui, see enums.py LocationKind
    def update_location(self, location):
        self.location = location
        self.updates.put(Change(UpdateKind.UPDATE_LOCATION, (location,)))
    
    # update the area of any user in the gui
    def update_user_rect(self, username, area):
        assert self.username is not None
        self.users[username] = area
    
    def delete_user(self, username):
        del self.users[username]

    # tell the gui to add a specific friend
    def add_friend(self, friend, accuracy=1):
        payload = (friend, accuracy)
        self.updates.put(Change(UpdateKind.ADD_FRIEND, (payload,)))

    # tell gui to remove a specific friend
    def remove_friend(self, friend):
        self.updates.put(Change(UpdateKind.REMOVE_FRIEND, (friend,)))

    def request_received(self, friend):
        self.updates.put(Change(UpdateKind.REQUEST_RECEIVED, (friend,)))

    # this is needed so the sliders in the gui can be instantiated correctly
    def update_spacial(self, area_steps):
        # area_steps ist eine liste mit den areas per depth level
        self.area_steps = area_steps
        self.updates.put(Change(UpdateKind.UPDATE_SPACIAL, (area_steps,)))
    
    # muss aufgerufen werden, damit die karte im gui sich updated
    def update_map(self):
        #(self.username, self.users)
        self.updates.put(Change(UpdateKind.UPDATE_MAP, (self.username, self.users,)))