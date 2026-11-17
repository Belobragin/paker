import pytest

from prutil import (
    get_all_labels,
    get_name_extension,
    local_get_class_idx,
    make_hyperparameters,
    message_is_valid,
    required_env,
)
from prutil.hyperparameters_default import BASE_EPS, STEPS_TARG, STEPS_UNTARG


def test_required_env_returns_set_value(monkeypatch):
    monkeypatch.setenv("AKER_TEST_VAR", "value")
    assert required_env("AKER_TEST_VAR") == "value"


def test_required_env_uses_default_when_unset(monkeypatch):
    monkeypatch.delenv("AKER_TEST_VAR", raising=False)
    assert required_env("AKER_TEST_VAR", "fallback") == "fallback"


@pytest.mark.parametrize("value", ["", "   "])
def test_required_env_rejects_blank_value(monkeypatch, value):
    monkeypatch.setenv("AKER_TEST_VAR", value)
    with pytest.raises(ValueError):
        required_env("AKER_TEST_VAR")


def test_required_env_rejects_missing_value_without_default(monkeypatch):
    monkeypatch.delenv("AKER_TEST_VAR", raising=False)
    with pytest.raises(ValueError):
        required_env("AKER_TEST_VAR")


def test_message_is_valid_accepts_untargeted_message():
    ok, err = message_is_valid({"order_id": "1", "algorythm": "fgsm"})
    assert ok is True
    assert err == ""


def test_message_is_valid_accepts_targeted_message_with_goal():
    ok, _ = message_is_valid(
        {"order_id": "1", "algorythm": "biterate_targeted", "alter_goal": "tiger_shark"}
    )
    assert ok is True


@pytest.mark.parametrize(
    "message, reason",
    [
        ({"algorythm": "fgsm"}, "order_id"),
        ({"order_id": "1"}, "algorythm"),
        ({"order_id": "1", "algorythm": "biterate_targeted"}, "alter goal"),
    ],
)
def test_message_is_valid_rejects_incomplete_message(message, reason):
    ok, err = message_is_valid(message)
    assert ok is False
    assert reason in err


def test_get_name_extension_splits_name_and_extension():
    assert get_name_extension("hog-test.jpg") == ("hog-test", "jpg")


def test_get_name_extension_uses_last_dot():
    assert get_name_extension("a.b.png") == ("b", "png")


def test_get_all_labels_covers_the_imagenet_classes():
    labels, classes = get_all_labels()
    # a few imagenet labels (crane, maillot) are shared by two classes
    assert len(labels) == len(classes) >= 990
    assert classes["tench"] == 0
    assert classes["tiger_shark"] == 3


def test_local_get_class_idx_known_and_unknown_label():
    assert local_get_class_idx("tiger_shark") == 3
    assert local_get_class_idx("not_an_imagenet_label") is None


def test_make_hyperparameters_defaults():
    params = make_hyperparameters({})
    assert params["base_eps"] == BASE_EPS
    assert params["steps_targ"] == STEPS_TARG
    assert params["steps_untarg"] == STEPS_UNTARG
    assert params["save_objects"] == 0


def test_make_hyperparameters_message_overrides_defaults():
    params = make_hyperparameters({"steps_untarg": 5, "base_eps": 0.5})
    assert params["steps_untarg"] == 5
    assert params["base_eps"] == 0.5
    assert params["steps_targ"] == STEPS_TARG
