# pyright: basic
import pytest

from lfg.group import Group
from lfg.role import Role
from lfg.state import State
from lfg.user import User


@pytest.fixture
def group() -> Group:
    roles = [Role.TANK, Role.HEALER, Role.DPS]
    return Group(
        "test_channel",
        User(
            user_id=123, user_name="", disc_name="", character="test_owner", roles=roles
        ),
    )


@pytest.fixture
def state() -> State:
    return State()


@pytest.fixture
def user() -> User:
    roles = [Role.TANK, Role.HEALER, Role.DPS]
    return User(
        user_id=123, user_name="", disc_name="", character="test_user", roles=roles
    )


def test_group_init(group: Group):
    test_user = User(
        user_id=123, user_name="", disc_name="", character="test_owner", roles=[]
    )
    assert group.channel == "test_channel"
    assert group.owner.user_id == test_user.user_id
    assert len(group.tank_queue) == 0
    assert len(group.healer_queue) == 0
    assert len(group.dps_queue) == 0


def test_group_owner(group: Group):
    assert group.is_owner(123)
    assert not group.is_owner(1234)
    group.set_owner(
        User(user_id=1234, user_name="", disc_name="", character="new_owner", roles=[])
    )
    assert group.is_owner(1234)
    assert not group.is_owner(123)


def test_group_add_user(group: Group):
    user1 = User(user_id=123, user_name="", disc_name="", character="user1", roles=[])
    user2 = User(user_id=1234, user_name="", disc_name="", character="user2", roles=[])
    user3 = User(user_id=12345, user_name="", disc_name="", character="user3", roles=[])

    group.add_tank(user1)
    group.add_tank(user1)
    group.add_dps(user1)
    group.add_healer(user1)
    group.add_dps(user2)
    group.add_healer(user2)
    group.add_healer(user3)

    tank_queue, healer_queue, dps_queue = group.get_queues()
    assert user1 in tank_queue
    assert user1 in healer_queue
    assert user1 in dps_queue
    assert user2 not in tank_queue
    assert user2 in healer_queue
    assert user2 in dps_queue
    assert user3 not in tank_queue
    assert user3 not in dps_queue
    assert user3 in healer_queue
    assert len(tank_queue) == 1


def test_group_remove_user(group: Group):
    user = User(
        user_id=123,
        user_name="test_user",
        disc_name="",
        character="dontmilkme",
        roles=[],
    )
    group.add_dps(user)

    assert len(group.dps_queue) == 1
    assert group.dps_queue[0].user_name == "test_user"

    returned_user = group.remove_user(user.user_id)

    assert len(group.dps_queue) == 0
    assert user not in group.dps_queue
    assert user == returned_user


def test_group_remove_character(group: Group, user: User):
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
