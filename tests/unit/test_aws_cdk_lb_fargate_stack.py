from aws_cdk import assertions, App, Environment
from aws_cdk_lb_fargate.aws_cdk_lb_fargate_stack import AwsCdkLbFargateStack
from aws_cdk_lb_fargate.config import config


def test_pypiserver_stack_created():
    app = App()
    env = Environment(account=config.account, region=config.region)
    stack = AwsCdkLbFargateStack(app, config, env=env)
    template = assertions.Template.from_stack(stack)

    template.has_resource_properties(
        "AWS::ECS::Service", {"LaunchType": "FARGATE"}
    )
