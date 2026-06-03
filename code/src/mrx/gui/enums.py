from enum import Enum, unique

@unique
class ChangeKind(Enum):
    LOCATION_UPDATE = 0
    LOGIN_TRIGGER = 1
    SIGNUP_TRIGGER = 2
    ACCURACY_UPDATE = 3
    MAP_INIT = 4
    CLOSE_WINDOW = 5

class Change:
    def __init__(self, kind: ChangeKind, attrs: tuple):
        self.kind = kind
        self.attrs = attrs

@unique
class LocationKind(Enum):
    # NOTE when updating this enum, make sure you also update the switch case statement in main.html and all the other ones
    LOGIN = 0
    SIGNUP = 1
    MAIN = 2

def from_number(cls: type[Enum], n: int):
    if not hasattr(cls, "_mapping") or cls._mapping is None: # type: ignore
        cls._mapping = {} # type: ignore
        mapping = dir(ChangeKind)
        for attr in mapping:
            if attr.startswith("_"):
                continue
            cls._mapping[ChangeKind[attr].value] = ChangeKind[attr] # type: ignore
    res = cls._mapping.get(n) # type: ignore
    if res is None:
        assert False, f"number {n} is not in enum {cls}. {cls._mapping}" # type: ignore
    return res