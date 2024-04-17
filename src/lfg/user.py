# pyright: basic
from lfg.role import Role


class User:
    def __init__(self, user_id: int, user_name: str, roles: list[Role]):
        # TODO: - figure out how to get user's discord server name
        #       - rename this class to toon or character? they can have multiple
        #         in the same queue
        # self.server_name = ""
        self.user_id = user_id
        self.user_name = user_name
        self.character_name = ""
        self.roles: list[Role] = roles

    def __eq__(self, other):
        return self.user_id == other.user_id

    def __str__(self):
        return f"User(user_name={self.user_name}, user_id={self.user_id}, character_name={self.character_name})"

    def __repr__(self):
        return f"User(user_name={self.user_name}, user_id={self.user_id}, character_name={self.character_name})"

    def set_character_name(self, name: str):
        self.character_name = name
        # self.invite_string = "/invite " + str(self.character_name)

    def get_invite_string(self) -> str | None:
        raise NotImplementedError
