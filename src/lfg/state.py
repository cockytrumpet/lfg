# pyright: basic
import pickle

from discord.ext import commands

from lfg.group import Group
from lfg.user import User
from lfg.utils import logger


class State:
    def __init__(self):
        super().__init__()
        self.groups: list[Group] = []
        self.users: dict[int, User] = {}

        self.reload_users()

    def reload_users(self):
        try:
            with open("state.users.pickle", "rb") as f:
                self.users = pickle.load(f)
        except FileNotFoundError:
            pass

    def update_user(self, user: User):
        """add/update to users dict"""
        self.users[user.id] = user
        with open("state.users.pickle", "wb") as f:
            pickle.dump(self.users, f)

    def get_user(self, ctx: commands.Context) -> User:
        """find user by context, calls update_user if not found"""
        user = self.users.get(ctx.message.author.id)
        if user is None:
            user = User(ctx)
            self.update_user(user)
        return user

    def get_user_by_id(self, id: int) -> User | None:
        """find user by id, doesn't call update_user"""
        user = self.users.get(id)
        return user or None

    def get_user_by_name(self, name: str) -> User | None:
        """find user by name or nick, doesn't call update_user"""
        if name == "":
            return None

        if name.startswith("<@"):
            user = self.get_user_by_id(int(name[2:-1]))
            return user

        for user in self.users.values():
            if user.name == name or user.nick == name:
                return user

        return None

    def get_user_by_character(self, character: str) -> User | None:
        """find user by character name, doesn't call update_user"""
        for user in self.users.values():
            for char in user.characters.keys():
                if char == character:
                    return user
        return None

    def add_group(self, channel: str, owner: User):
        """create new group and add it to groups list"""
        logger(channel, f"Create group '{channel}' with owner {owner.name}")
        new_group = Group(channel, owner)
        self.groups.append(new_group)

    def remove_group(self, channel: str):
        """remove group from groups list by channel name"""
        group = self.get_group(channel)
        if group:
            logger(
                group.channel,
                f"Remove group '{group.channel}' with owner {group.owner.name}",
            )
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
        char_list = []
        for user in self.users.values():
            for char in user.characters:
                char_list.append(char.__str__())

        return f"State({self.groups}, {', '.join(char_list)})"
