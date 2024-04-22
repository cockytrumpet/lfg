# pyright: basic
from lfg.role import Role
from lfg.user import User


class Task:
    def __init__(
        self,
        user: User,
        character: str,
    ):
        self.user: User = user
        self.character: str = character
        self.roles: list[Role] = self.user.characters.get(character, [])

    def __eq__(self, other):
        return self.user.id == other.user.id and self.character == other.character

    def __str__(self):
        if self.character != None:
            return f"{self.character} (*{self.user.name}*)"
        else:
            return f"{self.user.name}"

    def __repr__(self):
        return f"Task(user={self.user}, character={str(self.character)})"
