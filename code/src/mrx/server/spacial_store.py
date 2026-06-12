from logic.geometry import get_quadrant, Rect, is_inside
from math import sin, pi

class SpacialStore:
    """convention: x =^= longitude; y =^= latitude"""
    def __init__(self, startrect: Rect):
        self.startrect = startrect
        self._user_path: dict[str, list[int]] = {}

    def insert(self, user_id: str, quad_sequence: list[int]):
        self._user_path[user_id] = quad_sequence

    def get_all_users(self) -> dict[str, Rect]:
        """this method should really be called get_all_user_areas but is
        called get_all_users because other code depends on it."""
        return {user: self.get_area(user) for user in self._user_path}

    def get_all_usernames(self) -> list[str]:
        return list(self._user_path)

    def get_user_paths(self) -> dict[str, list[int]]:
        return self._user_path

    def has_user(self, user_id: str) -> bool:
        return user_id in self._user_path

    def remove_user(self, user_id: str):
        del self._user_path[user_id]

    def get_path(self, user_id: str) -> list[int]:
        return self._user_path[user_id]

    # THATS WHY HES THE GOAT, ... THE GOATTTT!!!
    # https://www.johndcook.com/blog/2023/02/21/sphere-grid-area/
    def get_accuracy_per_depth(self, num_accuracies) -> list[float]:
        """returns a list, where the i-th element corresponds to an estimate*
        of the area of regions at depth i. The unit of this list is km^2. <br>
        *: this is only an estimate, because regions defined by this
        partitioning at a certain depth can have different areas depending on
        their latitude; A latitude-longitude "rectangle" at the north-pole for
        example has a smaller area than the same "rectangle" at the equator.
        """
        r = 6_371 # radius of the earth in km
        total_area = \
               r**2 \
            * (sin(self.startrect.y_max / 180 * pi) - sin(self.startrect.y_min / 180 * pi)) \
            * (self.startrect.x_max - self.startrect.x_min) / 180 * pi
        accuracy_list = []
        curr_area = total_area
        for _ in range(num_accuracies):
            accuracy_list.append(curr_area)
            curr_area *= 0.25
        return accuracy_list

    def location_to_path(self, x, y, depth):
        res = []
        cur_rect = self.startrect
        for i in range(depth):
            for q in range(4):
                r = get_quadrant(cur_rect, q)
                assert r is not None
                if is_inside(r, x, y):
                    res.append(q)
                    cur_rect = r
                    break
        return res

    def path_to_rect(self, path):
        """returns None if there was an invalid quadrant in the path"""
        cur_rect = self.startrect
        for q in path:
            cur_rect = get_quadrant(cur_rect, q)
            if cur_rect is None:
                return None
        return cur_rect

    def get_area(self, user_id: str, accuracy: int = -1) -> Rect:
        """
        an accuracy of 0 means the lowest possible accuracy (the start rect is returned).
        if accuracy is less than 0, we return the rectangle with the maximuma
        accuracy.
        """
        if accuracy < 0:
            return self.startrect
        path = self._user_path[user_id][:accuracy]
        res = self.path_to_rect(path)
        assert res is not None
        return res