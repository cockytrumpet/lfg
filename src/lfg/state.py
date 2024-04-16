from collections import deque
from enum import Enum, auto
from typing import override


class Role(Enum):
    TANK = auto()
    HEALER = auto()
    DPS = auto()


class Group:
    def __init__(self, channel: str, owner: str):
        super().__init__()
        self.channel: str = channel
        self.owner: str = owner
        self.tank_queue: deque[str] = deque()
        self.healer_queue: deque[str] = deque()
        self.dps_queue: deque[str] = deque()

    def set_owner(self, owner: str):
        self.owner = owner

    def is_owner(self, member: str) -> bool:
        return member == self.owner

    def add_tank(self, member: str):
        self.tank_queue.append(member)

    def add_healer(self, member: str):
        self.healer_queue.append(member)

    def add_dps(self, member: str):
        self.dps_queue.append(member)

    def remove_member(self, member: str):
        for queue in [self.tank_queue, self.healer_queue, self.dps_queue]:
            if member in queue:
                queue.remove(member)

    def get_members(self) -> tuple[deque[str], deque[str], deque[str]]:
        return (self.tank_queue, self.healer_queue, self.dps_queue)

    def __repr__(self) -> str:
        return f"""
        Group(channel={self.channel},
              owner={self.owner},
              tank_queue={self.tank_queue},
              healer_queue={self.healer_queue},
              dps_queue={self.dps_queue})"
        """


class State:
    def __init__(self):
        super().__init__()
        self.groups: list[Group] = []

    def add_group(self, channel: str, owner: str):
        """create new group and add it to groups list"""
        new_group = Group(channel, owner)
        self.groups.append(new_group)

    def remove_group(self, channel: str):
        """remove group from groups list by channel name"""
        for group in self.groups:
            if group.channel == channel:
                self.groups.remove(group)
                del group

    def get_group(self, channel: str) -> Group | None:
        """find group by channel name"""
        for group in self.groups:
            if group.channel == channel:
                return group
        return None

    def get_groups(self):
        """return all groups as list[Group]"""
        return self.groups
