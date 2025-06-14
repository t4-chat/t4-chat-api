from enum import Enum


class UserGroupType(str, Enum):
    INDIVIDUAL = "individual"
    TEAM = "team"


class UserGroupName(str, Enum):
    BASIC = "basic"
