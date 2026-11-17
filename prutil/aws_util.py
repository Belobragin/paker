import boto3


def get_stack_output(stack_name, output_key):
    """return the value of a CloudFormation stack output, KeyError if it is absent"""
    stack = boto3.client("cloudformation").describe_stacks(StackName=stack_name)["Stacks"][0]
    value = next((o["OutputValue"] for o in stack.get("Outputs", []) if o["OutputKey"] == output_key), None)
    if value is None:
        raise KeyError(f"output {output_key} not found in stack {stack_name}")
    return value
