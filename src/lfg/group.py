# pyright: basic
from collections import deque

from lfg.user import User


class Group:
    def __init__(self, channel: str, owner: User):
        super().__init__()
        self.channel: str = channel
        self.owner: User = owner
        self.tank_queue: deque[User] = deque()
        self.healer_queue: deque[User] = deque()
        self.dps_queue: deque[User] = deque()

    def set_owner(self, owner: User):
        self.owner = owner

    def is_owner(self, user_id: int) -> bool:
        return self.owner.user_id == user_id

    def add_tank(self, member: User):
        if member not in self.tank_queue:
            self.tank_queue.append(member)

    def add_healer(self, member: User):
        if member not in self.healer_queue:
            self.healer_queue.append(member)

    def add_dps(self, member: User):
        if member not in self.dps_queue:
            self.dps_queue.append(member)

    def remove_member(self, member: User) -> User | None:
        for queue in [self.tank_queue, self.healer_queue, self.dps_queue]:
            if member in queue:
                queue.remove(member)
                return member

    def get_members(self) -> tuple[deque[User], deque[User], deque[User]]:
        return (self.tank_queue, self.healer_queue, self.dps_queue)

    def __repr__(self) -> str:  # pyright: ignore
        return f"Group(channel={self.channel}, owner={self.owner}, tank_queue={self.tank_queue}, healer_queue={self.healer_queue}, dps_queue={self.dps_queue})"
