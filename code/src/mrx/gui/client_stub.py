from .model import Model

class ClientStub:
    def __init__(self):
        self.model = Model(self)
    
    def handle_location(self, location):
        self.model.update_location(location)
    
    def handle_login(self, username, password):
        self.model.update_user(username=username)
        self.model.update_location(2)
    
    def handle_signup(self, username, password):
        self.model.update_user(username=username)
        self.model.update_location(2)
    
    def handle_accuracy(self, accuracy):
        self.model.update_user(accuracy=accuracy)
        self.model.update_map()
    
    def handle_init_map(self):
        self.model.update_map()

def main():
    c = ClientStub()

    user = ["alex", [47.3745, 8.5445], 200]
    others = {
            "pascal" : ([47.373, 8.545], 300), 
            "max" : ([47.379, 8.54], 100)
        }
    
    c.model.set_user(user)
    c.model.set_others(others)
    c.model.gui.start()