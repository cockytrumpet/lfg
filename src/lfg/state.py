# pyright: basic
from lfg.group import Group
from lfg.user import User


class State:
    def __init__(self):
        super().__init__()
        self.groups: list[Group] = []

    def add_group(self, channel: str, owner: User):
        """create new group and add it to groups list"""
        print(f"* Created group '{channel}' with owner {owner}")
        new_group = Group(channel, owner)
        self.groups.append(new_group)

    def remove_group(self, channel: str):
        """remove group from groups list by channel name"""
        print(f"* Removed group '{channel}'")
        self.groups = [group for group in self.groups if group.channel != channel]

    def get_group(self, channel: str) -> Group | None:
        """find group by channel name"""
        for group in self.groups:
            if group.channel == channel:
                return group
        return None

    def get_groups(self):
        """return all groups as list[Group]"""
        return self.groups

    def __str__(self):
        return f"{len(self.groups)} group(s): {', '.join(str(group.channel) for group in self.groups)}"

    def __repr__(self):
        return f"State({self.groups})"
