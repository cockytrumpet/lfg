from lfg.group import Group
from lfg.role import Role
from lfg.state import State
from lfg.user import Task

t = [Role.TANK]
h = [Role.HEALER]
d = [Role.DPS]

user1 = Task(
    user_id=1,
    user_name="Adam",
    disc_name="adam",
    character="maerah",
    roles=d + t,
)
user2 = Task(
    user_id=2,
    user_name="Adam",
    disc_name="adam",
    character="holysocks",
    roles=h,
)
user3 = Task(
    user_id=1,
    user_name="Adam",
    disc_name="adam",
    character="maerah",
    roles=h,
)
user4 = Task(
    user_id=3,
    user_name="Dave",
    disc_name="dave123",
    character="deadlyforce",
    roles=t,
)
user5 = Task(
    user_id=4,
    user_name="gil",
    disc_name="gil123",
    character="shammy",
    roles=h + d,
)

state = State()
state.add_group("ch1", user1)
group = state.get_group("ch1")

for user in [user1, user2, user3, user4, user5]:
    for group_role in user.roles:
        match group_role:
            case Role.TANK:
                group.add_tank(user)
            case Role.HEALER:
                group.add_healer(user)
            case Role.DPS:
                group.add_dps(user)

print(state)
print(group)
