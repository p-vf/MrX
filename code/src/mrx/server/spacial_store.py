from logic.geometry import get_quadrant, Rect

class SpacialStore:
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

    def get_path(self, user_id: str) -> list[int]:
        return self._user_path[user_id]

    def get_area(self, user_id: str, accuracy: int = -1) -> Rect:
        """
        an accuracy of 0 means the lowest possible accuracy (the start rect is returned).
        if accuracy is less than 0, we return the rectangle with the maximum
        accuracy.
        """
        curr_rect = self.startrect
        if accuracy == 0:
            return self.startrect
        path = self._user_path[user_id][:accuracy]
        for choice in path:
            curr_rect = get_quadrant(curr_rect, choice)
            assert curr_rect is not None
        return curr_rect