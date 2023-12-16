from aws_cdk import assertions, App, Environment
from nimbus_lib.stacks.bastion_stack import BastionStack
from nimbus_lib import config as confs


def test_bastion_stack_created():
    config = confs.BastionConfig(
        key_pair_name="fake",
        vpc_id="fake",
        stack_name="TestBastion",
        env="test",
        account="fake",
        region="us-east-1",
    )
    app = App()
    env = Environment(account=config.account, region=config.region)
    stack = BastionStack(app, config, env=env)
    template = assertions.Template.from_stack(stack)

    template.has_resource_properties(
        "AWS::EC2::Instance", {"SourceDestCheck": False}
    )
