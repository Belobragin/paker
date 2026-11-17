import json

from algo import AlteritAlgoName, AlteritBackMessage


def test_algorythm_names_match_the_message_values():
    assert AlteritAlgoName.fgsm_algo == "fgsm"
    assert AlteritAlgoName.basic_iterative_targeted == "biterate_targeted"
    assert AlteritAlgoName.basic_iterative_untargeted == "biterate_untargeted"


def test_back_message_serializes_filter_name_only_when_filter_saved():
    saved = json.loads(
        AlteritBackMessage("1", True, True, "adv.jpg", "flt.jpg", "fgsm", "", {}).serialize()
    )
    not_saved = json.loads(
        AlteritBackMessage("1", True, False, "adv.jpg", "flt.jpg", "fgsm", "", {}).serialize()
    )
    assert saved["filter_name"] == "flt.jpg"
    assert "filter_name" not in not_saved


def test_back_message_error_defaults_to_empty_string():
    message = json.loads(AlteritBackMessage("1", True, False, "a", "", "fgsm", "", {}).serialize())
    assert message["error"] == ""
    assert "timestamp" in message
