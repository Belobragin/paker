import pytest

from prutil import get_stack_output


class _FakeCloudFormation:
    def __init__(self, outputs):
        self._outputs = outputs
        self.requested_stack = None

    def describe_stacks(self, StackName):
        self.requested_stack = StackName
        return {"Stacks": [{"Outputs": self._outputs}]}


@pytest.fixture
def fake_cloudformation(monkeypatch):
    client = _FakeCloudFormation(
        [{"OutputKey": "WerewolfProjectBucketName", "OutputValue": "bucket-1"}]
    )
    monkeypatch.setattr("prutil.aws_util.boto3.client", lambda service: client)
    return client


def test_get_stack_output_returns_value_of_the_key(fake_cloudformation):
    assert get_stack_output("werewolf-stack", "WerewolfProjectBucketName") == "bucket-1"
    assert fake_cloudformation.requested_stack == "werewolf-stack"


def test_get_stack_output_raises_key_error_for_absent_key(fake_cloudformation):
    with pytest.raises(KeyError):
        get_stack_output("werewolf-stack", "NoSuchOutput")
