# pyright: basic
import pytest

from lfg.group import Group
from lfg.role import Role
from lfg.state import State
from lfg.task import Task
from lfg.user import User


@pytest.fixture
def user() -> User:
    return User()


@pytest.fixture
def group(user: User) -> Group:
    return Group("test_channel", user)


@pytest.fixture
def state() -> State:
    return State()


@pytest.fixture
def task(user: User) -> Task:
    roles = [Role.TANK, Role.HEALER, Role.DPS]
    return Task(user=user, character="test_user")


def test_group_init(user: User):
    group = Group("test_channel", user)
    assert group.channel == "test_channel"
    assert group.owner.id == user.id
    assert len(group.tank_queue) == 0
    assert len(group.healer_queue) == 0
    assert len(group.dps_queue) == 0


def test_group_owner(group: Group, user: User):
    group.set_owner(user)
    assert group.is_owner(0)


def test_group_add_user(user: User, group: Group):
    task1 = Task(user=user, character="user1")
    task2 = Task(user=user, character="user2")
    task3 = Task(user=user, character="user3")

    group.add_tank(task1)
    group.add_tank(task1)
    group.add_dps(task1)
    group.add_healer(task1)
    group.add_dps(task2)
    group.add_healer(task2)
    group.add_healer(task3)

    tank_queue, healer_queue, dps_queue = group.get_queues()
    assert task1 in tank_queue
    assert task1 in healer_queue
    assert task1 in dps_queue
    assert task2 not in tank_queue
    assert task2 in healer_queue
    assert task2 in dps_queue
    assert task3 not in tank_queue
    assert task3 not in dps_queue
    assert task3 in healer_queue
    assert len(tank_queue) == 1


def test_group_remove_user(group: Group, user: User):
    task = Task(
        # user_id=123,
        # user_name="test_user",
        # disc_name="",
        user=user,
        character="dontmilkme",
    )
    group.add_dps(task)

    assert len(group.dps_queue) == 1
    assert group.dps_queue[0].character == "dontmilkme"

    returned_user = group.remove_user(task.user.id)

    assert len(group.dps_queue) == 0
    assert task not in group.dps_queue
    assert task.user == returned_user


def test_group_remove_character(group: Group, user: Task):
    assert len(group.tank_queue) == 0
    assert len(group.healer_queue) == 0
    assert len(group.dps_queue) == 0
    group.tank_queue.append(user)
    group.healer_queue.append(user)
    group.dps_queue.append(user)
    assert len(group.tank_queue) == 1
    assert len(group.healer_queue) == 1
    assert len(group.dps_queue) == 1
    group.remove_character(user)
