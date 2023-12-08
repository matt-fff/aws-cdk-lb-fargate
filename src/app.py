#!/usr/bin/env python3

import aws_cdk as cdk

from aws_cdk_lb_fargate.aws_cdk_lb_fargate_stack import AwsCdkLbFargateStack
from aws_cdk_lb_fargate.config import config


app = cdk.App()
env = cdk.Environment(account=config.account, region=config.region)
AwsCdkLbFargateStack(app, config, env=env)

app.synth()
