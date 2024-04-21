# pyright: basic
import pytest

from lfg.group import Group
from lfg.state import State
from lfg.user import User


@pytest.fixture
def user2() -> User:
    return User()


@pytest.fixture
def user() -> User:
    return User()


@pytest.fixture
def group(user: User) -> Group:
    return Group(
        "test_channel",
        user,
    )


@pytest.fixture
def state() -> State:
    return State()


def test_state_init(state: State):
    assert len(state.groups) == 0


def test_state_add_group(state: State, user: User):
    state.add_group("test_channel", user)
    assert len(state.groups) == 1
    assert state.groups[0].channel == "test_channel"
    assert state.groups[0].owner == user


def test_state_remove_group(state: State, user: User, user2: User):
    assert len(state.groups) == 0
    state.add_group("test_channel", user)
    assert len(state.groups) == 1
    state.add_group("test_channel2", user2)
    assert len(state.groups) == 2
    state.remove_group("test_channel2")
    assert len(state.groups) == 1
    state.remove_group("test_channel")
    assert len(state.groups) == 0


def test_state_get_group(state: State, user: User):
    state.add_group("test_channel", user)
    group = state.get_group("test_channel")
    if group is None:
        assert False
    assert group.channel == "test_channel"
    assert group.owner == user
