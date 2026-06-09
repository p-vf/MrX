
import json

class Quadrant:
    NW = 0
    NE = 1
    SW = 2
    SE = 3

class Rect:
    def __init__(self, x_min: float, y_min: float, x_max: float, y_max: float):
        self.x_min = x_min
        self.y_min = y_min
        self.x_max = x_max
        self.y_max = y_max

    def __repr__(self):
        return f"Rect({self.x_min}, {self.y_min}, {self.x_max}, {self.y_max})"

def get_quadrant(r: Rect, quad: int) -> Rect | None:
    # NOTE (p-vf) there is a high chance that either north and south or east
    # and west are swapped but this is okay, as it doesn't matter if we just
    # stay consistent.
    x_min = r.x_min
    y_min = r.y_min
    x_max = r.x_max
    y_max = r.y_max
    x_mid = (r.x_max + r.x_min) / 2
    y_mid = (r.y_max + r.y_min) / 2
    match quad:
        case Quadrant.NE:
            x_max = x_mid
            y_max = y_mid
        case Quadrant.NW:
            x_min = x_mid
            y_max = y_mid
        case Quadrant.SE:
            x_max = x_mid
            y_min = y_mid
        case Quadrant.SW:
            x_min = x_mid
            y_min = y_mid
        case _:
            return None
    return Rect(x_min, y_min, x_max, y_max)

def to_json_serializable(rect: Rect) -> dict:
    return dict(x_min=rect.x_min, y_min=rect.y_min, x_max=rect.x_max, y_max=rect.y_max)

def serialize_rect(rect: Rect) -> str:
    return json.dumps([rect.x_min, rect.y_min, rect.x_max, rect.y_max])

def deserialize_rect(data: str) -> Rect:
    x_min, y_min, x_max, y_max = json.loads(data)
    return Rect(x_min, y_min, x_max, y_max)

def is_inside(rect: Rect, x, y):
    return rect.x_min <= x < rect.x_max and rect.y_min <= y < rect.y_max

if __name__ == "__main__":
    for i in range(4):
        print(f"{get_quadrant(Rect(0, 0, 1, 1), i)=}, {i=}")

