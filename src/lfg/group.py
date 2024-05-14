# pyright: basic
from collections import deque
from datetime import datetime
from typing import Counter

from lfg.role import Role
from lfg.task import Task
from lfg.user import User
from lfg.utils import logger


class Pretty_deque(deque):
    def __repr__(self):
        return f"{list(self)}"

    def __str__(self):
        return f"{list(self)}"


class Vote:
    def __init__(self, candidate: User):
        self.candidate = candidate
        self.timestamp = datetime.now()

    def __repr__(self) -> str:
        return str(self.candidate)

    def __str__(self) -> str:
        return f"Vote({self.candidate})"


class Group:
    def __init__(self, channel: str, owner: User):
        super().__init__()
        self.channel: str = channel
        self.owner: User = owner
        self.votes: deque[Vote] = Pretty_deque()
        self.tank_queue: deque[Task] = Pretty_deque()
        self.healer_queue: deque[Task] = Pretty_deque()
        self.dps_queue: deque[Task] = Pretty_deque()

    def set_owner(self, owner: User):
        logger(self.channel, f"Set owner to {owner}")
        self.owner = owner

    def is_owner(self, user_id: int) -> bool:
        return self.owner.id == user_id

    def add_vote(self, candidate: User):
        self.votes.append(Vote(candidate))

    def check_votes(self) -> User | None:
        now = datetime.now()

        while len(self.votes) > 0 and (now - self.votes[0].timestamp).seconds > 10:
            _ = self.votes.popleft()

        counter = dict()
        for vote in self.votes:
            if vote.candidate in counter:
                counter[vote.candidate] += 1
            else:
                counter[vote.candidate] = 1

        if len(counter) != 0:
            max_votes = max(counter.values())
            if max_votes > len(self.votes) // 2:
                for candidate, votes in counter.items():
                    if votes == max_votes:
                        return candidate

        return None

    def add_tank(self, task: Task):
        if task not in self.tank_queue:
            logger(self.channel, f"Added {task} to tank queue")
            self.tank_queue.append(task)

    def add_healer(self, task: Task):
        if task not in self.healer_queue:
            logger(self.channel, f"Added {task} to healer queue")
            self.healer_queue.append(task)

    def add_dps(self, task: Task):
        if task not in self.dps_queue:
            logger(self.channel, "* Added {task} to DPS queue")
            self.dps_queue.append(task)

    def next_tank(self) -> Task | None:
        if len(self.tank_queue) == 0:
            return None

        next_task = self.tank_queue.popleft()
        self.remove_character(next_task)
        return next_task

    def next_healer(self) -> Task | None:
        if len(self.healer_queue) == 0:
            return None

        next_task = self.healer_queue.popleft()
        self.remove_character(next_task)
        return next_task

    def next_dps(self) -> Task | None:
        if len(self.dps_queue) == 0:
            return None

        next_task = self.dps_queue.popleft()
        self.remove_character(next_task)
        return next_task

    def remove_character(
        self, task: Task, roles: list[Role] = [Role.TANK, Role.HEALER, Role.DPS]
    ) -> bool:
        def total_tasks() -> int:
            return len(self.tank_queue) + len(self.healer_queue) + len(self.dps_queue)

        start_count = total_tasks()
        r_str = ""

        for role in roles:
            match role:
                case Role.TANK:
                    if task in self.tank_queue:
                        self.tank_queue.remove(task)
                        r_str += "T"
                case Role.HEALER:
                    if task in self.healer_queue:
                        self.healer_queue.remove(task)
                        r_str += "H"
                case Role.DPS:
                    if task in self.dps_queue:
                        self.dps_queue.remove(task)
                        r_str += "D"

        if r_str:
            r_str = f"from [{','.join(r_str)}]"

        logger(self.channel, f"Remove {task} {r_str}")
        return start_count == total_tasks()

    def remove_user(self, user_id: int) -> bool:
        removed = False
        for queue in [self.tank_queue, self.healer_queue, self.dps_queue]:
            user: User | None = None
            temp = []

            for task in queue:
                if task.user.id == user_id:
                    if not user:
                        user = task.user
                    temp.append(task)

            if len(temp) > 0:
                removed = True

            for t in temp:
                if t in queue:
                    queue.remove(t)

        if user:
            logger(self.channel, f"Remove {user.nick} from queues")

        return removed

    def get_queues(self) -> tuple[deque[Task], deque[Task], deque[Task]]:
        return (self.tank_queue, self.healer_queue, self.dps_queue)

    def __repr__(self) -> str:  # pyright: ignore
        return f"Group(channel={self.channel}, owner={self.owner}, votes={self.votes}, tank_queue={self.tank_queue}, healer_queue={self.healer_queue}, dps_queue={self.dps_queue})"

    def __str__(self) -> str:  # pyright: ignore
        tank = list(self.tank_queue)
        healer = list(self.healer_queue)
        dps = list(self.dps_queue)

        t_len = len(tank)
        h_len = len(healer)
        d_len = len(dps)
        max_len = max(t_len, h_len, d_len)

        output = f'{"#":<4} {"**Tank**":<20} {"**Healer**":<20} {"**DPS**":<20}\n'  # pyright: ignore
        output += "-" * len(output) + "\n"

        for i in range(max_len, -1, -1):
            tank_str = tank[i].__str__() if i < t_len else ""
            healer_str = healer[i].__str__() if i < h_len else ""
            dps_str = dps[i].__str__() if i < d_len else ""
            if tank_str + healer_str + dps_str == "":
                continue

            output += f"{i+1:<4} {tank_str:<20} {healer_str:<20} {dps_str:<20}\n"

        return output or "NO OUTPUT"
