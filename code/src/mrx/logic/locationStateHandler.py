from ..communication.common import StateHandler
from .protocol import encode_message, decode_message

# msg to client
# {
#   "type": "quadrant_question",
#   "area": {
#     "x_min": 0,
#     "y_min": 0,
#     "x_max": 100,
#     "y_max": 100
#   }
# }

class LocationStateHandler(StateHandler):

    def __init__(self, quadtree):
        self.tree = quadtree
        self.current_node = quadtree

    def handle(self, data, reply_callback):

        msg = decode_message(data)

        vertical = msg["vertical"]
        horizontal = msg["horizontal"]

        self.current_node.subdivide()

        self.current_node = self.current_node.get_quadrant(
            vertical,
            horizontal
        )

        response = {
            "type": "quadrant_question",
            "area": self.current_node.boundary.to_dict()
        }

        reply_callback(encode_message(response))

    def end(self):
        print("client disconnected")