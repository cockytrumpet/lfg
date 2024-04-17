# pyright: basic
import pytest

from lfg.group import Group
from lfg.state import State
from lfg.user import User


@pytest.fixture
def group() -> Group:
    return Group("test_channel", User(user_id=123, user_name="test_owner"))


@pytest.fixture
def state() -> State:
    return State()


def test_group_init(group: Group):
    test_user = User(user_id=123, user_name="test_owner")
    assert group.channel == "test_channel"
    assert group.owner.user_id == test_user.user_id
    assert group.owner.user_name == test_user.user_name
    assert len(group.tank_queue) == 0
    assert len(group.healer_queue) == 0
    assert len(group.dps_queue) == 0


def test_group_owner(group: Group):
    assert group.is_owner(123)
    assert not group.is_owner(1234)
    group.set_owner(User(user_id=1234, user_name="new_owner"))
    assert group.is_owner(1234)
    assert not group.is_owner(123)


def test_group_add_member(group: Group):
    user1 = User(user_id=123, user_name="user1")
    user2 = User(user_id=1234, user_name="user2")
    user3 = User(user_id=12345, user_name="user3")

    group.add_tank(user1)
    group.add_tank(user1)
    group.add_dps(user1)
    group.add_healer(user1)
    group.add_dps(user2)
    group.add_healer(user2)
    group.add_healer(user3)

    tank_queue, healer_queue, dps_queue = group.get_members()
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


def test_group_remove_member(group: Group):
    user = User(user_id=123, user_name="test_user")
    group.add_dps(user)

    assert len(group.dps_queue) == 1
    assert group.dps_queue[0].user_name == "test_user"

    returned_user = group.remove_member(user)

    assert len(group.dps_queue) == 0
    assert user not in group.dps_queue
    assert user == returned_user


def test_state_init(state: State):
    assert len(state.groups) == 0


def test_state_add_group(state: State):
    state.add_group("test_channel", "test_owner")
    assert len(state.groups) == 1
    assert state.groups[0].channel == "test_channel"
    assert state.groups[0].owner == "test_owner"


def test_state_remove_group(state: State):
    state.add_group("test_channel", "test_owner")
    state.remove_group("test_channel")
    assert len(state.groups) == 0


def test_state_get_group(state: State):
    state.add_group("test_channel", "test_owner")
    group = state.get_group("test_channel")
    if group is None:
        assert False
    assert group.channel == "test_channel"
    assert group.owner == "test_owner"
