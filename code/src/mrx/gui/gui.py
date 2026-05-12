import webview
import os
import folium
import time

BACKGROUND = "#1e1e1e"
BUTTON = "#3a3a3a"
BUTTON_PRESS = "#505050"
TEXT = "#ffffff"

class Gui:
    def __init__(self):
        path = os.path.abspath("src/mrx/gui/login.html")
        self.api = Api()

        self.window = webview.create_window(
            "MrX",
            path,
            js_api = self.api
        )

    def run(self):
        webview.start()

    def generate_map(self, location, zoom, users):
        map = folium.Map(
            location=location,
            zoom_start=zoom,
            tiles="CartoDB positron"
        )

        for user in users:
            folium.Circle(
                user,
                radius=1000,
                color="blue",
                fill=True,
            ).add_to(map)

        map.save("src/mrx/gui/map.html")
    
class Api:
    def __init__(self):
        self.accuracy = 100
        self.username = ""
        self.password = ""

    def login(self, username, password):
        self.username = username
        self.password = password
        return 0
    
    def signup(self, username, password):
        self.username = username
        self.password = password
        return 0
    
    def set_accuracy(self, accuracy):
        try:
            self.accuracy = int(accuracy)
            return 0
        except:
            return 1

def main():
    gui = Gui()
    location = [47.3769, 8.5417]
    users = [[47.3745, 8.5445]]
    gui.generate_map(location, 12, users)
    gui.run()
