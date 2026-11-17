import json
import re
from pathlib import Path

import pytest

IAC = Path(__file__).resolve().parent.parent / "iac" / "awscloud"


def _declared_parameters(template):
    """names under the top-level Parameters: block of a CloudFormation yaml"""
    text = (IAC / "template" / template).read_text(encoding="utf-8")
    block = text.split("\nParameters:\n", 1)[1].split("\nResources:", 1)[0]
    return set(re.findall(r"^  (\w+):\s*$", block, flags=re.MULTILINE))


def _load(name):
    return json.loads((IAC / "parameter" / name).read_text(encoding="utf-8"))


@pytest.mark.parametrize(
    "parameter_file, template",
    [
        ("aker-ecs-parameter.json", "AkerEcsTemplate.yaml"),
        ("aker-ecr-parameter.json", "AkerEcrTemplate.yaml"),
    ],
)
def test_cli_parameter_file_only_sets_declared_parameters(parameter_file, template):
    entries = _load(parameter_file)
    assert isinstance(entries, list)
    assert {e["ParameterKey"] for e in entries} <= _declared_parameters(template)


@pytest.mark.parametrize(
    "parameter_file, template",
    [
        ("aker_resource_pipeline_parameter.json", "AkerEcsTemplate.yaml"),
        ("aker-service-parameter.json", "AkerServiceTemplate.yaml"),
    ],
)
def test_pipeline_parameter_file_only_sets_declared_parameters(parameter_file, template):
    content = _load(parameter_file)
    assert set(content) == {"Parameters"}
    assert set(content["Parameters"]) <= _declared_parameters(template)


def test_service_template_parameters_are_covered_by_the_pipeline():
    """ImageUri and AppVersion are the only service parameters without a default, the pipeline sets them"""
    text = (IAC / "template" / "AkerServiceTemplate.yaml").read_text(encoding="utf-8")
    block = text.split("\nParameters:\n", 1)[1].split("\nResources:", 1)[0]
    without_default = set()
    for name, body in re.findall(r"^  (\w+):\n((?:    .*\n)+)", block, flags=re.MULTILINE):
        if "Default:" not in body:
            without_default.add(name)
    assert without_default == {"ImageUri", "AppVersion"}
