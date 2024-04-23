# pyright: basic
from discord.ext import commands

from lfg.role import Role


class User:
    def __init__(self, ctx: commands.Context | None = None):
        super().__init__()

        if ctx:
            id: int = ctx.message.author.id
            name: str | None = ctx.message.author.global_name
            nick: str | None = ctx.message.author.nick
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
        self.characters[character] = roles

    def get_last_roles(self, character: str) -> list[Role]:
        if character in self.characters:
            return self.characters[character]
        return []

    def get_characters(self) -> dict[str, list[Role]]:
        return self.characters

    def __eq__(self, other):
        return self.id == other.id

    def __str__(self):
        return self.nick

    def __repr__(self):
        return f"User(id={self.id}, name={self.name}, nick={self.nick}, guild_id={self.guild_id}, character_list={self.characters})"
