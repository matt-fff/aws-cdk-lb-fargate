from aws_cdk import assertions, App, Environment
from nimbus_lib.stacks.fargate_stack import FargateStack
from nimbus_lib.config import config


def test_fargate_stack_created():
    app = App()
    env = Environment(account=config.account, region=config.region)
    stack = FargateStack(app, config, env=env)
    template = assertions.Template.from_stack(stack)

    template.has_resource_properties(
        "AWS::ECS::Service", {"LaunchType": "FARGATE"}
    )
