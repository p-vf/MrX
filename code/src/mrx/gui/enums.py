from enum import Enum, unique

@unique
class ChangeKind(Enum):
    LOCATION_UPDATE = 0
    LOGIN_TRIGGER = 1
    SIGNUP_TRIGGER = 2
    ACCURACY_UPDATE = 3
    MAP_INIT = 4
    ADD_FRIEND = 5
    REMOVE_FRIEND = 6
    ACCEPT_REQUEST = 7
    CLOSE_WINDOW = 8

@unique
class UpdateKind(Enum):
    OFFLINE = -1
    UPDATE_LOCATION = 0
    UPDATE_MAP = 1
    ADD_FRIEND = 2
    REMOVE_FRIEND = 3
    REQUEST_RESPONSE = 4
    REQUEST_RECEIVED = 5
    UPDATE_SPACIAL = 6
    INIT_FRIENDLIST = 7

@unique
class AnswerKind(Enum):
    ACCEPT = 0
    DENY = 1

class Change:
    def __init__(self, kind: ChangeKind, attrs: tuple):
        self.kind = kind
        self.attrs = attrs

    def __repr__(self):
        return f"Change({self.kind}, {self.attrs})"

@unique
class LocationKind(Enum):
    # NOTE when updating this enum, make sure you also update the switch case statement in main.html and all the other ones
    LOGIN = 0
    SIGNUP = 1
    MAIN = 2

def from_number(cls: type[Enum], n: int):
    if not hasattr(cls, "_mapping") or cls._mapping is None: # type: ignore
        cls._mapping = {} # type: ignore
        mapping = dir(cls)
        for attr in mapping:
            if attr.startswith("_"):
                continue
            cls._mapping[cls[attr].value] = cls[attr] # type: ignore
    res = cls._mapping.get(n) # type: ignore
    if res is None:
        assert False, f"number {n} is not in enum {cls}. {cls._mapping}" # type: ignore
    return res