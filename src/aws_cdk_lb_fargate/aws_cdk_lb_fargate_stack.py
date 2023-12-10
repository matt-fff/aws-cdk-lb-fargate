from typing import Any
from aws_cdk_lb_fargate.stacks import LBFargateStack
from aws_cdk_lb_fargate.config import Config


class AwsCdkLbFargateStack(LBFargateStack[Config]):
    def image_environment(self, config: Config) -> dict[str, Any]:
        return {
            "ENV": config.env,
        }
