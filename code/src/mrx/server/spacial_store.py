from logic.geometry import get_quadrant, Rect

class SpacialStore:
    def __init__(self, startrect: Rect):
        self.startrect = startrect
        self.user_rect: dict[str, Rect] = {}

    def insert(self, user_id: str, quad_sequence: list[int]):
        curr_rect = self.startrect
        for choice in quad_sequence:
            curr_rect = get_quadrant(curr_rect, choice)
            assert curr_rect is not None

        self.user_rect[user_id] = curr_rect

    def get_all_users(self):
        return self.user_rect

    def get_area(self, user_id: str) -> Rect:
        return self.user_rect[user_id]