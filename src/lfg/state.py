from lfg.group import Group
from lfg.user import User


class State:
    def __init__(self):
        super().__init__()
        self.groups: list[Group] = []

    def add_group(self, channel: str, owner: User):
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
