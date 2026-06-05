from .gui import Gui
from gui.types import BaseModel
from logic.geometry import Rect
from gui.enums import UpdateKind, AnswerKind, Change

class Model(BaseModel):
    def __init__(self, client):
        self.location = 0
        self.username: str | None = None
        self.userarea: Rect | None = None
        self.useraccuracy: float | None = None
        self.others: dict[str, Rect] = {}
        self.accuracy_bounds: tuple[int, int] = None

        self.gui = Gui(client)
        self.updates = self.gui.get_update_queue()
    
    def start_gui(self):
        self.gui.start()

    def get_others(self):
        return self.others
    
    def set_user(self, username: str):
        self.username = username
    
    def set_others(self, others):
        self.others = others
    
    def update_location(self, location):
        self.location = location
        self.updates.put(Change(UpdateKind.UPDATE_LOCATION, (location,)))
    
    def update_user_rect(self, username, area):
        assert self.username is not None
        if username == self.username:
            self.userarea = area
        else:
            self.others[username] = area
        self.updates.put(Change(UpdateKind.UPDATE_MAP, (self.userarea, self.others)))
    
    def insert_others(self, username, area):
        self.others[username] = area
    
    def delete_others(self, username):
        del self.others[username]

    def add_friend(self, friend):
        self.updates.put(Change(UpdateKind.ADD_FRIEND, (friend,)))

    def remove_friend(self, friend):
        self.delete_others(friend)
        self.updates.put(Change(UpdateKind.REMOVE_FRIEND, (friend,)))
    
    def request_response(self, friend, answer):
        if (answer == AnswerKind.ACCPET):
            self.insert_others(friend, None)
        
        self.updates.put(Change(UpdateKind.REQUEST_RESPONSE, (friend, answer)))    

    def update_spacial(self, min_area, max_area):
        self.accuracy_bounds = (min_area, max_area)
        self.updates.put(Change(UpdateKind.UPDATE_SPACIAL, (self.accuracy_bounds[0], self.accuracy_bounds[1],)))
    
    def update_others(self, old_un, new_un=None, position=None, accuracy=None):
        # NOTE (p-vf) I think we don't have to handle changing usernames as this
        # might lead to unnecessary complexity. As far as I know, there are no
        # security benefits to this feature but idk.
        curr_pos, curr_acc = self.others[old_un]
        curr_un = old_un

        if new_un:
            curr_un = new_un
            del self.others[old_un]

        if position:
            curr_pos = position
        
        if accuracy:
            curr_acc = accuracy
        
        self.others[curr_un] = (curr_pos, curr_acc)
    
    def update_map(self):
        self.updates.put(Change(UpdateKind.UPDATE_MAP, (self.userarea, self.others)))