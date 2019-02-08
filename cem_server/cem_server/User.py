from enum import Enum

class UserState(Enum):
    UNKNOWN = 0
    NOTHING_RESERVED = 1
    WAITING_RESOURCES = 2
    RESOURCES_ASSIGNED = 3
    ACTIVE = 4