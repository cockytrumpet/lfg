# pyright: basic
from discord.ext import commands

from lfg.group import Group
from lfg.role import Role
from lfg.user import User
from lfg.utils import logger


class State:
    def __init__(self):
        super().__init__()
        self.groups: list[Group] = []
        # NOTE: maybe figure out persistent storage for this
        self.users: dict[int, User] = {}

    def update_user(self, user: User):
        """add/update to users dict"""
        self.users[user.id] = user

    def get_user(self, user_id: int) -> User | None:
        """find user by id"""
        return self.users.get(user_id, None)

    def add_group(self, channel: str, owner: User):
        """create new group and add it to groups list"""
        logger(channel, f"Create group '{channel}' with owner {owner.name}")
        new_group = Group(channel, owner)
        self.groups.append(new_group)

    def remove_group(self, ctx: commands.Context):
        """remove group from groups list by channel name"""
        logger(
            ctx.channel.name,
            f"Remove group '{ctx.channel}' with owner {ctx.message.author.global_name}",
        )
        self.groups = [group for group in self.groups if group.channel != ctx.channel]

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
