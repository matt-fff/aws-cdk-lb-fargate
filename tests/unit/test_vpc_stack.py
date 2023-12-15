from aws_cdk import assertions, App, Environment
from nimbus_lib.stacks.vpc_stack import VpcStack
from nimbus_lib import config as confs


def test_vpc_stack_created():
    config = confs.VpcConfig(
        stack_name="TestVpc",
        env="test",
        account="fake",
        region="us-east-1",
    )
    app = App()
    env = Environment(account=config.account, region=config.region)
    stack = VpcStack(app, config, env=env)
    template = assertions.Template.from_stack(stack)

    template.has_resource_properties(
        "AWS::EC2::VPC", {"EnableDnsHostnames": True}
    )
