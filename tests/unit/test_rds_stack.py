from aws_cdk import assertions, App, Environment
from nimbus_lib.stacks.rds_stack import RdsStack
from nimbus_lib import config as confs


def test_rds_stack_created():
    config = confs.RdsConfig(
        vpc_id="fake",
        stack_name="TestRds",
        env="test",
        account="fake",
        region="us-east-1",
        db_port=5432,
    )
    app = App()
    env = Environment(account=config.account, region=config.region)
    stack = RdsStack(app, config, env=env)
    template = assertions.Template.from_stack(stack)

    template.has_resource_properties(
        "AWS::RDS::DBInstance",
        {"Engine": "postgres", "PubliclyAccessible": False},
    )
