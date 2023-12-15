from aws_cdk import assertions, App, Environment
from nimbus_lib.stacks.fargate_stack import FargateStack
from nimbus_lib import config as confs


def test_fargate_stack_created():
    config = confs.FargateConfig(
        stack_name="TestFargate",
        env="test",
        account="fake",
        region="us-east-1",
        vpc_id="fake",
        container=confs.ContainerConfig(
            port=80,
            image="fake",
        ),
    )
    app = App()
    env = Environment(account=config.account, region=config.region)
    stack = FargateStack(app, config, env=env)
    template = assertions.Template.from_stack(stack)

    template.has_resource_properties(
        "AWS::ECS::Service", {"LaunchType": "FARGATE"}
    )
