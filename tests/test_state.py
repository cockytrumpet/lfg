# pyright: basic

import pytest

from ..src.lfg.state import Group, State


@pytest.fixture
def group() -> Group:
    return Group("test_channel", "test_owner")


@pytest.fixture
def state() -> State:
    return State()


def test_group_init(group: Group):
    assert group.channel == "test_channel"
    assert group.owner == "test_owner"
    assert len(group.tank_queue) == 0
    assert len(group.healer_queue) == 0
    assert len(group.dps_queue) == 0


def test_group_owner(group: Group):
    assert group.is_owner("test_owner")
    assert not group.is_owner("not_owner")
    group.set_owner("new_owner")
    assert group.is_owner("new_owner")
    assert not group.is_owner("test_owner")


def test_group_add_member(group: Group):
    group.add_tank("test_tank")
    group.add_healer("test_healer")
    group.add_dps("test_dps")
    assert "test_tank" in group.tank_queue
    assert "test_healer" in group.healer_queue
    assert "test_dps" in group.dps_queue


def test_group_remove_member(group: Group):
    group.add_tank("test_user")
    group.add_healer("test_user")
    group.add_dps("test_user")
    group.remove_member("test_user")
    assert "test_user" not in group.tank_queue
    assert "test_user" not in group.healer_queue
    assert "test_user" not in group.dps_queue


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
