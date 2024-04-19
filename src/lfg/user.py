# pyright: basic
from lfg.role import Role


class User:
    def __init__(
        self,
        user_id: int,
        user_name: str,
        disc_name: str,
        character: str,
        roles: list[Role],
    ):
        # TODO:
        #       - rename this class to toon or character? they can have multiple
        #         in the same queue
        self.user_id: int = user_id
        self.user_name: str = user_name
        self.disc_name: str = disc_name
        self.character: str = character
        self.roles: list[Role] = roles

    def __eq__(self, other):
        return self.user_id == other.user_id and self.character == other.character

    def __str__(self):
        if self.character != None:
            return f"{self.character} (*{self.user_name}*)"
        else:
            return f"{self.user_name}"

    def __repr__(self):
        return f"User(user_id={self.user_id}, user_name={self.user_name}, disc_name={self.disc_name}, character={self.character}, roles={self.roles})"
