# pyright: basic
from lfg.role import Role
from lfg.user import User


class Task:
    def __init__(
        self,
        user: User,
        character: str,
        roles: list[Role],
    ):
        self.user: User = user
        self.character: str = character
        self.roles: list[Role] = roles

    # TODO: decide the best way forward
    #       - best way to cache past char/roles?
    #       - when and how to update?

    def __eq__(self, other):
        return self.user.id == other.user.id and self.character == other.character

    def __str__(self):
        if self.character != None:
            return f"{self.character} (*{self.user.name}*)"
        else:
            return f"{self.user.name}"

    def __repr__(self):
        return f"Task(user={self.user}, character={self.character}, roles={self.roles})"
