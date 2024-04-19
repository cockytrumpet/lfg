# pyright: basic
from collections import deque

from lfg.role import Role
from lfg.user import User


class Pretty_deque(deque):
    def __repr__(self):
        return f"{list(self)}"

    def __str__(self):
        return f"{list(self)}"


class Group:
    def __init__(self, channel: str, owner: User):
        super().__init__()
        self.channel: str = channel
        self.owner: User = owner
        self.tank_queue: deque[User] = Pretty_deque()
        self.healer_queue: deque[User] = Pretty_deque()
        self.dps_queue: deque[User] = Pretty_deque()

    def set_owner(self, owner: User):
        print("* Set owner to {owner}")
        self.owner = owner

    def is_owner(self, user_id: int) -> bool:
        return self.owner.user_id == user_id

    def add_tank(self, user: User):
        if user not in self.tank_queue:
            print(f"* Added {user} to tank queue")
            self.tank_queue.append(user)

    def add_healer(self, user: User):
        if user not in self.healer_queue:
            print(f"* Added {user} to healer queue")
            self.healer_queue.append(user)

    def add_dps(self, user: User):
        if user not in self.dps_queue:
            print(f"* Added {user} to DPS queue")
            self.dps_queue.append(user)

    def next_tank(self) -> User | None:
        if len(self.tank_queue) == 0:
            return None

        next = self.tank_queue.popleft()
        self.remove_character(next)
        return next

    def next_healer(self) -> User | None:
        if len(self.healer_queue) == 0:
            return None

        next = self.healer_queue.popleft()
        self.remove_character(next)
        return next

    def next_dps(self) -> User | None:
        if len(self.dps_queue) == 0:
            return None

        next = self.dps_queue.popleft()
        self.remove_character(next)
        return next

    def remove_character(
        self, user: User, roles: list[Role] = [Role.TANK, Role.HEALER, Role.DPS]
    ) -> User | None:
        print(f"* Removing {user} from [", end="")
        for role in roles:
            match role:
                case Role.TANK:
                    if user in self.tank_queue:
                        print("T", end="")
                        self.tank_queue.remove(user)
                case Role.HEALER:
                    if user in self.healer_queue:
                        print("H", end="")
                        self.healer_queue.remove(user)
                case Role.DPS:
                    if user in self.dps_queue:
                        print("D", end="")
                        self.dps_queue.remove(user)
        print("]")
        return user

    def remove_user(self, user_id: int) -> User | None:
        for queue in [self.tank_queue, self.healer_queue, self.dps_queue]:
            user = None
            temp = []
            for q in queue:
                if q.user_id == user_id:
                    if not user:
                        user = q
                    temp.append(q)
            for t in temp:
                if t in queue:
                    queue.remove(t)

        print(f"* Removed {user_id=} from queues")
        return user

    def get_queues(self) -> tuple[deque[User], deque[User], deque[User]]:
        return (self.tank_queue, self.healer_queue, self.dps_queue)

    def __repr__(self) -> str:  # pyright: ignore
        return f"Group(channel={self.channel}, owner={self.owner}, tank_queue={self.tank_queue}, healer_queue={self.healer_queue}, dps_queue={self.dps_queue})"

    def __str__(self) -> str:  # pyright: ignore
        tank = list(self.tank_queue)
        healer = list(self.healer_queue)
        dps = list(self.dps_queue)

        t_len = len(tank)
        h_len = len(healer)
        d_len = len(dps)
        max_len = max(t_len, h_len, d_len)

        output = f'{"\#":<4} {"**Tank**":<20} {"**Healer**":<20} {"**DPS**":<20}\n'
        output += "-" * len(output) + "\n"

        for i in range(max_len, -1, -1):
            tank_str = tank[i].__str__() if i < t_len else ""
            healer_str = healer[i].__str__() if i < h_len else ""
            dps_str = dps[i].__str__() if i < d_len else ""
            if tank_str + healer_str + dps_str == "":
                continue

            output += f"{i+1:<4} {tank_str:<20} {healer_str:<20} {dps_str:<20}\n"

        return output or "NO OUTPUT"
