import asyncio
import json
import logging

import pytest

from algo import AttackError
from bus.cloud import cloud_proc

logger = logging.getLogger("aker-test")


def _process(message):
    raw = message if isinstance(message, str) else json.dumps(message)
    return json.loads(asyncio.run(cloud_proc.process_message_cloud(raw, logger, False)))


def test_process_message_rejects_non_json_body():
    reply = _process("not a json")
    assert reply["success_adversarial"] is False
    assert "json" in reply["error"]


def test_process_message_rejects_zero_order_id():
    reply = _process({"order_id": 0, "algorythm": "fgsm"})
    assert reply["success_adversarial"] is False
    assert "order_id" in reply["error"]


def test_process_message_rejects_targeted_attack_without_goal():
    reply = _process({"order_id": "1", "algorythm": "biterate_targeted", "input_image_name": "a.jpg"})
    assert reply["success_adversarial"] is False
    assert "alter goal" in reply["error"]


def test_process_message_reports_attack_failure_with_order_id(monkeypatch):
    class _FailingAttack:
        def __init__(self, **kwargs):
            raise AttackError("boom")

    monkeypatch.setattr(cloud_proc, "CloudAttack", _FailingAttack)
    reply = _process(
        {"order_id": "42", "algorythm": "fgsm", "input_image_name": "a.jpg", "save_filter": "1"}
    )
    assert reply["order_id"] == "42"
    assert reply["success_adversarial"] is False
    assert reply["error"] == "boom"


def test_process_message_returns_predictions_of_a_successful_attack(monkeypatch):
    class _Attack:
        def __init__(self, **kwargs):
            self.save_filter = kwargs["save_filter"]

        def generate_attack(self):
            pass

        def save_final_image_to_storage(self):
            pass

        def get_from_attack(self):
            return {"n0": ["n01440764", "tench", "0", "99.0"]}

        def get_adv_name(self):
            return "storage/adversarial/a_adversarial_fgsm.jpg"

        def get_filter_name(self):
            return "storage/filter/a_filter_fgsm.jpg"

    monkeypatch.setattr(cloud_proc, "CloudAttack", _Attack)
    reply = _process(
        {"order_id": "7", "algorythm": "fgsm", "input_image_name": "a.jpg", "save_filter": "1"}
    )
    assert reply["success_adversarial"] is True
    assert reply["adversarial_name"].endswith("a_adversarial_fgsm.jpg")
    assert reply["predictions"]["n0"][1] == "tench"
