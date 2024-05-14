# pyright: basic
from typing import Optional

import discord
from discord import SelectOption
from discord.ext import commands

from lfg.role import Role


class User:
    def __init__(self, ctx: discord.ApplicationContext | None = None):
        super().__init__()

        if ctx:
            id: int = ctx.author.id
            name: str | None = ctx.author.global_name
            nick: str | None = ctx.author.nick
            guild_id: int = ctx.guild.id
            characters: dict[str, list[Role]] = {}
        else:
            id: int = 0
            name: str | None = ""
            nick: str | None = ""
            guild_id: int = 0
            characters: dict[str, list[Role]] = {}

        self.id: int = id
        self.name: str | None = name
        self.nick: str | None = nick
        self.guild_id: int = guild_id
        self.characters: dict[str, list[Role]] = characters

    def add_character(self, character: str, roles: list[Role]):
        """add to user.characters dict"""
        if not roles:
            return
        if roles:
            self.characters[character] = roles

    def get_last_roles(self, character: str) -> list[Role]:
        if character in self.characters:
            return self.characters[character]
        return []

    def get_characters(self) -> dict[str, list[Role]]:
        return self.characters

    @classmethod
    def roles_to_str(cls, roles: list[Role]) -> str:
        ret_str = ""
        for role in roles:
            match role:
                case Role.TANK:
                    ret_str += "t"
                case Role.HEALER:
                    ret_str += "h"
                case Role.DPS:
                    ret_str += "d"
        return ret_str

    @classmethod
    def str_to_roles(cls, role_str: str) -> list[Role]:
        roles = set()
        for letter in role_str:
            match letter.lower():
                case "t":
                    roles.add(Role.TANK)
                case "h":
                    roles.add(Role.HEALER)
                case "d":
                    roles.add(Role.DPS)
        return list(roles)

    def get_select_options(self) -> list[SelectOption] | None:
        options: list[SelectOption] = []
        for name, roles in self.characters.items():
            if roles:
                roles = self.roles_to_str(roles)
                options.append(SelectOption(label=name, value=f"{name}.{roles}"))
            else:
                assert False
        return options

    def __eq__(self, other):
        return self.id == other.id

    def __str__(self):
        return self.nick

    def __repr__(self):
        return f"User(id={self.id}, name={self.name}, nick={self.nick}, guild_id={self.guild_id}, character_list={self.characters})"

    def __hash__(self):
        print(hash(str(self)))
        return hash(str(self))
