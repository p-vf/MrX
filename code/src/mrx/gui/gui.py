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
        )
        if w is None:
            raise Exception("Window could not be created")
        self.window = w

        self.window.events.closed += self.on_closed
        self.generate_map([47.3745, 8.5445], 5)

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
            print(f"CHANGE: {change}")
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
                case ChangeKind.ACCURACY_OTHERS_UPDATE:
                    assert len(change.attrs) == 2
                    self.client.handle_others_accuracy(*change.attrs)
                case ChangeKind.MAP_INIT:
                    assert len(change.attrs) == 0
                    self.client.handle_init_map()
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
            print(f"UPDATE: {update}")
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
                case UpdateKind.INIT_FRIENDLIST:
                    assert len(update.attrs) == 1
                    self.init_friendlist(*update.attrs)
                case x:
                    assert False, f"unreachable: {x} not handled"
        except queue.Empty:
            pass

    def update_location(self, location: LocationKind):
        self.window.state.location = location.value
        self.window.evaluate_js(f"update_location()")

    def update_map(self, user: Rect, others: dict[str, Rect]):
        self.window.state.user_rect = to_json_serializable(user)
        self.window.state.other_user_rects = [[o, to_json_serializable(others[o])] for o in others]
        self.window.evaluate_js("update_map()")

    def update_accuracy(self, accuracy):
        # TODO prevent possible js-injection here..
        self.window.evaluate_js(f"update_accuracy({accuracy})")

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

    def init_friendlist(self, friends):
        self.window.state.friends = friends
        self.window.state.requests = []
        self.window.evaluate_js("update_friendlist()")

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
                console.log(user)
                console.log(others)

                const user_id = "you";
                const others_id = others.map(o => o[0]);


                var bounds = [[user.x_min, user.y_min], [user.x_max, user.y_max]];

                console.log(`adding rect for friend: ${user_id}`);
                if (!window.markers.has(user_id)) {
                    let new_user_a = L.rectangle(bounds, {color: "green", weight: 1});
                    new_user_a.addTo(window.marker_lyr);
                    window.markers.set(user_id, new_user_a);
                } else {
                    let old_user_c = window.markers.get(user_id);
                    old_user_c.setBounds(bounds)
                }

                console.log("added user marker");


                for (let i = 0; i < others.length; i++) {
                    rect = others[i][1]
                    other_id = others[i][0]
                    var bounds = [[rect.x_min, rect.y_min], [rect.x_max, rect.y_max]];
                    console.log(`adding rect for friend: ${other_id}`);
                    if (!window.markers.has(other_id)) {
                        let new_user_a = L.rectangle(bounds, {color: "blue", weight: 1});
                        new_user_a.addTo(window.marker_lyr);
                        window.markers.set(other_id, new_user_a);
                    } else {
                        let old_user_c = window.markers.get(user_id);
                        old_user_c.setBounds(bounds)
                    }
                }

                console.log("added others markers");

                const keep = new Set([
                    user_id,
                    ...others_id
                ]);

                for (const id of window.markers.keys()) {
                    console.log(`checking rect for friend: ${id}`);
                    if (!keep.has(id)) {
                        console.log(`removing rect for friend: ${id}`);
                        window.marker_lyr.removeLayer(window.markers.get(id));
                        window.markers.delete(id);
                    } else {
                        window.markers.get(id).bindTooltip(id, {
                            permanent : true,
                            direction : 'top'
                        }).openTooltip();
                    }
                }

                console.log("removed old markers");
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

    def update_client_init_map(self):
        self.changes.put(Change(ChangeKind.MAP_INIT, ()))
    
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