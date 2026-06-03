import webview
import branca
import os
import folium
import time
import queue
from typing import Any
import threading

from gui.types import BaseClient
from gui.enums import LocationKind, ChangeKind, from_number, Change


BACKGROUND = "#1e1e1e"
BUTTON = "#3a3a3a"
BUTTON_PRESS = "#505050"
TEXT = "#ffffff"

class Gui:
    def __init__(self, client: BaseClient):
        path = os.path.abspath("src/mrx/gui/login.html")
        self.changes: queue.Queue[Change] = queue.Queue()
        self.updates: queue.Queue[tuple] = queue.Queue()
        self.online = True

        self.api = Api(self.changes)
        self.client = client

        w = webview.create_window(
            "MrX",
            path,
            js_api = self.api,
        )
        if w is None:
            raise Exception("Window could not be created")
        self.window = w

        self.window.events.closed += self.on_closed
        self.generate_map([47.3745, 8.5445], 12)

    def get_update_queue(self):
        return self.updates

    def on_closed(self):
        self.updates.put((-1,))

    def start(self):
        webview.start(debug=True, func=self.communication)

    def communication(self):
        while self.online:
            self.check_changes()
            self.check_updates()
            time.sleep(0.1)

    def check_changes(self):
        try:
            change = self.changes.get(block=False)
            match change.kind:
                case ChangeKind.LOCATION_UPDATE:
                    assert len(change.attrs) == 1
                    self.client.handle_location(*change.attrs)
                case ChangeKind.LOGIN_TRIGGER:
                    assert len(change.attrs) == 2
                    self.client.handle_login(*change.attrs)
                case ChangeKind.SIGNUP_TRIGGER:
                    assert len(change.attrs) == 2
                    self.client.handle_signup(*change.attrs)
                case ChangeKind.ACCURACY_UPDATE:
                    assert len(change.attrs) == 1
                    self.client.handle_accuracy(*change.attrs)
                case ChangeKind.MAP_INIT:
                    assert len(change.attrs) == 0
                    self.client.handle_init_map()
                case x:
                    assert False, f"unreachable: {x} not handled"
        except queue.Empty:
            pass

    def check_updates(self):
        try:
            update = self.updates.get(block=False)

            match update[0]:
                case -1:
                    self.online = False
                case 0:
                    self.update_location(update[1])
                case 1:
                    self.update_map(update[1], update[2])
                case 2:
                    self.update_accuracy(update[1])
                case x:
                    assert False, f"unreachable: {x} not handled"
        except queue.Empty:
            pass

    def update_location(self, location):
        self.window.evaluate_js(f"update_location({location})")

    def update_map(self, user, others):
        self.window.evaluate_js(f"update_map({user}, {others})")

    def update_accuracy(self, accuracy):
        self.window.evaluate_js(f"update_accuracy({accuracy})")

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

            async function update_map(user, others) {
                console.log(user);
                console.log(others);

                const user_id = user[0];
                const others_id = others.map(o => o[0]);

                let new_user_c = L.circle(
                    user[1], {
                    radius : user[2],
                    color : "green",
                    fill : true
                })

                if (!window.markers.has(user_id)) {
                    new_user_c.addTo(window.marker_lyr);
                    window.markers.set(user_id, new_user_c);
                } else {
                    let old_user_c = window.markers.get(user_id);
                    if (
                        old_user_c.getLatLng() != new_user_c.getLatLng() ||
                        old_user_c.getRadius() != new_user_c.getRadius()
                        ) {
                        new_user_c.addTo(window.marker_lyr);
                        window.marker_lyr.removeLayer(window.markers.get(user_id))
                        window.markers.set(user_id, new_user_c);
                    }
                }

                for (let i = 0; i < others.length; i++) {
                    let new_other_c = L.circle(
                        others[i][1], {
                        radius : others[i][2],
                        color : "blue",
                        fill : true
                    })

                    if (!window.markers.has(others_id[i])) {
                        new_other_c.addTo(window.marker_lyr);
                        window.markers.set(others_id[i], new_other_c);
                    } else {
                        let old_other_c = window.markers.get(others_id[i]);
                        if (
                            old_other_c.getLatLng() != new_other_c.getLatLng() ||
                            old_other_c.getRadius() != new_other_c.getRadius()
                            ) {
                            new_other_c.addTo(window.marker_lyr);
                            window.marker_lyr.removeLayer(window.markers.get(others_id[i]))
                            window.markers.set(others_id[i], new_other_c);
                        }
                    }
                }

                const keep = new Set([
                    user_id,
                    ...others_id
                ]);

                for (const id of window.markers.keys()) {
                    if (!keep.has(id)) {
                        window.marker_lyr.removeLayer(window.markers.get(id));
                        window.markers.delete(id);
                    } else {
                        window.markers.get(id).bindTooltip(id, {
                            permanent : true,
                            direction : 'top'
                        }).openTooltip();
                    }
                }
            }
        </script>
        """
        root = map.get_root()
        assert isinstance(root, branca.element.Figure), f"unexpected element type of root: {type(root)}"
        root.html.add_child(folium.Element(js))
        map.save("src/mrx/gui/map.html")

class Api:
    def __init__(self, changes: queue.Queue[Change]):
        self.changes = changes

    def update_client_location(self, location):
        self.changes.put(Change(ChangeKind.LOCATION_UPDATE, (location,)))

    def update_client_login(self, username, password):
        self.changes.put(Change(ChangeKind.LOGIN_TRIGGER, (username, password)))

    def update_client_signup(self, username, password):
        self.changes.put(Change(ChangeKind.SIGNUP_TRIGGER, (username, password)))

    def update_client_accuracy(self, accuracy):
        self.changes.put(Change(ChangeKind.ACCURACY_UPDATE, (accuracy,)))

    def update_client_init_map(self):
        self.changes.put(Change(ChangeKind.MAP_INIT, ()))

    def close_client(self):
        self.changes.put(Change(ChangeKind.CLOSE_WINDOW, ()))