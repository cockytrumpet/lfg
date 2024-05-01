# for debugging use with ipython -i repl.py

from lfg.role import Role
from lfg.state import State
from lfg.task import Task
from lfg.user import User

state = State()

t = [Role.TANK]
h = [Role.HEALER]
d = [Role.DPS]

user1 = User()
user1.name = "Adam"
user1.nick = "adam"

user2 = User()
user2.name = "Dave"
user2.nick = "DeadlyForce"

user3 = User()
user3.name = "Gil"
user3.nick = "gilguy"

user1.add_character("maerah", d)
user2.add_character("deadlyforce", t)
user3.add_character("shammy", h + d)

tasks: list[Task] = [
    Task(
        user=user1,
        character="maerah",
    ),
    Task(
        user=user2,
        character="deadlyforce",
    ),
    Task(
        user=user3,
        character="shammy",
    ),
]

state.update_user(user1)
state.update_user(user2)
state.update_user(user3)
state.add_group("alpha", user1)
group = state.get_group("alpha")

if group:
    for task in tasks:
        for role in task.roles:
            match role:
                case Role.TANK:
                    group.add_tank(task)
                case Role.HEALER:
                    group.add_healer(task)
                case Role.DPS:
                    group.add_dps(task)

print(state)
