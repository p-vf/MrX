import webview
import os
import folium
import json

BACKGROUND = "#1e1e1e"
BUTTON = "#3a3a3a"
BUTTON_PRESS = "#505050"
TEXT = "#ffffff"

class Gui:
    def __init__(self, client, users):
        path = os.path.abspath("src/mrx/gui/login.html")
        self.api = Api(client, users)

        self.window = webview.create_window(
            "MrX",
            path,
            js_api = self.api
        )

    def run(self):
        self.api.update_map()
        webview.start(debug=True)

    def generate_map(self, location, zoom):
        map = folium.Map(
            location=location,
            zoom_start=zoom,
            tiles="CartoDB positron"
        )

        js = """
        <script>
            function getFoliumMap() {
                return Object.values(window)
                    .find(v => v && v instanceof L.Map);
            }

            async function init() {
                window.map = getFoliumMap();
                window.marker_lyr = L.layerGroup().addTo(map);

                const response = await fetch("data.json");
                const data = await response.json();

                window.markers = new Map();
            }

            async function update_map() {

                const response = await fetch("data.json");
                const data = await response.json();

                const client = data.client;
                const users = data.users;

                const client_id = `${client.pos[0]}-${client.pos[1]}-${client.acc}`;
                const user_id = [];

                for (let i = 0; i < users.length; i++) {
                    user_id.push(`${users[i].pos[0]}-${users[i].pos[1]}-${users[i].acc}`)
                }

                if (!window.markers.has(client_id)) {
                    let circle = L.circle(
                        client.pos, {
                        radius : client.acc,
                        color : "green",
                        fill : true
                    }).addTo(window.marker_lyr);

                    window.markers.set(client_id, circle)
                }

                for (let i = 0; i < users.length; i++) {
                    if (!window.markers.has(user_id[i])) {
                        let circle = L.circle(
                            users[i].pos, {
                            radius : users[i].acc,
                            color : "blue",
                            fill : true
                        }).addTo(window.marker_lyr);

                        window.markers.set(user_id[i], circle);
                    }
                }
                
                const keep = new Set([
                    client_id,
                    ...user_id
                ]);

                for (const id of window.markers.keys()) {

                    if (!keep.has(id)) {
                        window.marker_lyr.removeLayer(window.markers.get(id));
                        window.markers.delete(id);
                    } 
                }
            }
        </script>
        """
        map.get_root().html.add_child(folium.Element(js))
        map.save("src/mrx/gui/map.html")

    def update_map(self, client, users):
        self.api.set_client(client)
        self.api.set_users(users)
        self.api.update_map()
    
class Api:
    # Make thread safe
    def __init__(self, client, users):
        self.users = users
        self.client = client
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
            self.client = (self.client[0], int(accuracy))
            self.update_map()
            return 0
        except:
            return 1
    
    def set_client(self, client):
        self.client = client
    
    def set_users(self, users):
        self.users = users
        
    def update_map(self):
        data = {
            "client" : {
                "pos" : self.client[0],
                "acc" : self.client[1]
            },
            "users": [
                {"pos": user[0], "acc": user[1]} for user in self.users
            ]
        }

        path = os.path.abspath("src\mrx\gui\data.json")
        with open(path, "w") as f:
            json.dump(data, f)

def main():
    location = [47.3769, 8.5417]
    users = [([47.3745, 8.5445], 200)]
    client = (([47.373, 8.545], 300))

    gui = Gui(client, users)
    gui.generate_map(location, 12)
    gui.run()
