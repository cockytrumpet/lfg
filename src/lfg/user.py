# pyright: basic
class User:
    def __init__(self, user_id: int, user_name: str):
        self.user_id = user_id
        self.user_name = user_name
        # TODO: figure out how to get user's server name instead of user_name'
        # self.server_name = server_name

    def __eq__(self, other):
        return self.user_id == other.user_id

    def __str__(self):
        return f"User(user_name={self.user_name}, user_id={self.user_id})"

    def __repr__(self):
        return f"User(user_name={self.user_name}, user_id={self.user_id})"
