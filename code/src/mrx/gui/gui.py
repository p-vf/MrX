import webview
import branca
import os
import folium
import time
import queue

from gui.types import BaseClient
from gui.enums import LocationKind, ChangeKind, UpdateKind, AnswerKind, from_number, Change
from logic.geometry import to_json_serializable, Rect


BACKGROUND = "#1e1e1e"
BUTTON = "#3a3a3a"
BUTTON_PRESS = "#505050"
TEXT = "#ffffff"

class Gui:
    def __init__(self, client: BaseClient):
        path = os.path.abspath("src/mrx/gui/login.html")
        self.changes: queue.Queue[Change] = queue.Queue()
        self.updates: queue.Queue[Change] = queue.Queue()
        self.online = True

        self.api = Api(self.changes)
        self.client = client

        w = webview.create_window(
            "MrX",
            path,
            js_api = self.api,
            maximized=True,
        )
        if w is None:
            raise Exception("Window could not be created")
        self.window = w

        self.window.state.requests = []
        self.window.events.closed += self.on_closed
        self.generate_map([46.6283, 8.3722], 8)

    def get_update_queue(self):
        return self.updates

    def on_closed(self):
        self.updates.put(Change(UpdateKind.OFFLINE, ()))

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
            #print(f"CHANGE: {change}")
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
                case ChangeKind.ACCURACY_OTHERS_UPDATE:
                    assert len(change.attrs) == 2
                    self.client.handle_others_accuracy(*change.attrs)
                case ChangeKind.READY:
                    assert len(change.attrs) == 0
                    self.client.handle_ready()
                case ChangeKind.ADD_FRIEND:
                    assert len(change.attrs) == 1
                    self.client.handle_add_friend(*change.attrs)
                case ChangeKind.REMOVE_FRIEND:
                    assert len(change.attrs) == 1
                    self.client.handle_remove_friend(*change.attrs)
                case ChangeKind.ACCEPT_REQUEST:
                    assert len(change.attrs) == 2
                    self.client.handle_accept_request(*change.attrs)
                case x:
                    assert False, f"unreachable: {x} not handled"
        except queue.Empty:
            pass

    def check_updates(self):
        try:
            update = self.updates.get(block=False)
            #print(f"UPDATE: {update}")
            match update.kind:
                case UpdateKind.OFFLINE:
                    self.online = False
                case UpdateKind.UPDATE_LOCATION:
                    assert len(update.attrs) == 1
                    self.update_location(*update.attrs)
                case UpdateKind.UPDATE_MAP:
                    assert len(update.attrs) == 2
                    self.update_map(*update.attrs)
                case UpdateKind.ADD_FRIEND:
                    assert len(update.attrs) == 1
                    self.add_friend(*update.attrs)
                case UpdateKind.REMOVE_FRIEND:
                    assert len(update.attrs) == 1
                    self.remove_friend(*update.attrs)
                case UpdateKind.REQUEST_RECEIVED:
                    assert len(update.attrs) == 1
                    self.request_received(*update.attrs)
                case UpdateKind.UPDATE_SPACIAL:
                    assert len(update.attrs) == 1
                    self.update_spacial(*update.attrs)
                case UpdateKind.LOGIN_FAILED:
                    assert len(update.attrs) == 1
                    self.login_failed(*update.attrs)
                case x:
                    assert False, f"unreachable: {x} not handled"
        except queue.Empty:
            pass

    def update_location(self, location: LocationKind):
        self.window.state.location = location.value
        self.window.evaluate_js(f"update_location()")

    def update_map(self, username: str, users: dict[str, Rect]):
        assert username is not None
        self.window.state.username = username
        self.window.state.user_rects = [[u, to_json_serializable(users[u])] for u in users]
        self.window.evaluate_js("update_map()")

    def add_friend(self, friend):
        self.window.state.friends = [friend]
        self.window.evaluate_js("update_friendlist()")

    def remove_friend(self, friend):
        self.window.state.remove = friend
        self.window.evaluate_js("update_remove_friend()")
    
    def request_received(self, friend):
        req_list = self.window.state.requests
        req_list = req_list + [friend] #append doesnt work!!!
        self.window.state.requests = req_list

    def update_spacial(self, area_steps):
        self.window.state.acc_steps = area_steps
    
    def login_failed(self, error_msg):
        self.window.state.login_error = error_msg
        self.window.evaluate_js("login_failed()")

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

            function strFromBounds(bounds) {
                const bounds_str = `${bounds[0][0]}-${bounds[0][1]}-${bounds[1][0]}-${bounds[1][1]}-`;
                return bounds_str;
            }

            async function update_map(username, users) {
                const users_id = users.map(u => u[0]);
                let overlapping = new Map()

                for (let i = 0; i < users.length; i++) {
                    rect = users[i][1]
                    user_id = users[i][0]
                    var bounds = [[rect.x_min, rect.y_min], [rect.x_max, rect.y_max]];

                    if (!window.markers.has(user_id)) {
                        let new_user_a = L.rectangle(bounds, {color: (user_id == username) ? "green" : "blue", weight: 1});
                        new_user_a.addTo(window.marker_lyr);
                        window.markers.set(user_id, new_user_a);
                    } else {
                        let old_user_c = window.markers.get(user_id);
                        old_user_c.setBounds(bounds)
                    }

                    if (overlapping.has(strFromBounds(bounds))) {
                        if (user_id == username) {
                            overlapping.get(strFromBounds(bounds)).push(user_id);
                        } else {
                            overlapping.get(strFromBounds(bounds)).unshift(user_id);
                        }
                    } else {
                        overlapping.set(strFromBounds(bounds), [user_id])
                    }
                }

                for (const id of window.markers.keys()) {
                    if (!users_id.includes(id)) {
                        window.marker_lyr.removeLayer(window.markers.get(id));
                        window.markers.delete(id);
                    } else {
                        const rect_bounds = window.markers.get(id).getBounds();
                        const sw = rect_bounds.getSouthWest();
                        const ne = rect_bounds.getNorthEast();

                        const bounds = [[sw.lat, sw.lng], [ne.lat, ne.lng]];
                        const names = overlapping.get(strFromBounds(bounds));

                        if (id == names.at(-1) ) {
                            names_str = "";

                            for (let i = 0; i < names.length; i++) {
                                if (i == names.length - 1) {
                                    names_str += names[i];
                                } else {
                                    names_str += names[i] + ", ";
                                }
                            }

                            window.markers.get(id).bindTooltip(names_str, {
                                permanent : true,
                                direction : 'top'
                            }).openTooltip();
                        } else {
                            window.marker_lyr.removeLayer(window.markers.get(id));
                            window.markers.delete(id);
                        }
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

    def update_client_location(self, location_int: int):
        self.changes.put(Change(ChangeKind.LOCATION_UPDATE, (from_number(LocationKind, location_int),)))

    def update_client_login(self, username, password):
        print("update_client_login fired")
        self.changes.put(Change(ChangeKind.LOGIN_TRIGGER, (username, password)))

    def update_client_signup(self, username, password):
        self.changes.put(Change(ChangeKind.SIGNUP_TRIGGER, (username, password)))

    def update_client_others_accuracy(self, friend, depth_level):
        self.changes.put(Change(ChangeKind.ACCURACY_OTHERS_UPDATE, (friend, depth_level,)))

    def update_client_ready(self):
        self.changes.put(Change(ChangeKind.READY, ()))
    
    def update_client_add_friend(self, friend):
        self.changes.put(Change(ChangeKind.ADD_FRIEND, (friend,)))
    
    def update_client_remove_friend(self, friend):
        self.changes.put(Change(ChangeKind.REMOVE_FRIEND, (friend,)))

    def update_client_accept_request(self, friend, answer):
        answer_kind = AnswerKind.ACCEPT
        if answer == 1:
            answer_kind = AnswerKind.DENY

        self.changes.put(Change(ChangeKind.ACCEPT_REQUEST, (friend, answer_kind,)))

    def close_client(self):
        self.changes.put(Change(ChangeKind.CLOSE_WINDOW, ()))