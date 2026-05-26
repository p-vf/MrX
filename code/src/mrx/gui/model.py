from .gui import Gui

class Model:
    def __init__(self, client):
        self.location = 0
        self.user = []
        self.others = {}

        self.gui = Gui(client)
        self.updates = self.gui.get_update_queue()
    
    def get_user(self):
        return self.user
    
    def get_others(self):
        return self.others
    
    def set_user(self, user):
        self.user = user
    
    def set_others(self, others):
        self.others = others
    
    def update_location(self, location):
        self.location = location
        self.updates.put((0, location))
    
    def update_user(self, username=None, position=None, accuracy=None):
        if username:
            self.user[0] = username
        
        if position:
            self.user[1] = position
        
        if accuracy:
            self.user[2] = accuracy
    
    def insert_others(self, username, position, accuracy):
        self.others[username] = (position, accuracy)
    
    def delete_others(self, username):
        del self.others[username]
    
    def update_others(self, old_un, new_un=None, position=None, accuracy=None):
        curr_pos, curr_acc = self.others[old_un]
        curr_un = old_un

        if new_un:
            curr_un = new_un
            del self.others["old_un"]

        if position:
            curr_pos = position
        
        if accuracy:
            curr_acc = accuracy
        
        self.others[curr_un] = (curr_pos, curr_acc)
    
    def update_map(self):
        others_list = []

        for key in self.others:
            pos, acc = self.others[key]
            others_list.append([key, pos, acc])

        self.updates.put((1, self.user, others_list))