#!/usr/bin/env python3

import aws_cdk as cdk

from nimbus_lib.nimbus_stack import NimbusStack
from nimbus_lib.config import config


app = cdk.App()
env = cdk.Environment(account=config.account, region=config.region)
NimbusStack(app, config, env=env)

app.synth()
