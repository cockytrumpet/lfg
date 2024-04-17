# pyright: basic
class User:
    def __init__(self, user_id: int, user_name: str):
        self.user_id = user_id
        self.user_name = user_name

    def __str__(self):
        return f"User(user_name={self.user_name}, user_id={self.user_id=})"
