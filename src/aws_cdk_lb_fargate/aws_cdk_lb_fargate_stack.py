from constructs import Construct
from aws_cdk import (
    CfnOutput,
    aws_ec2 as ec2,
)
from aws_cdk_lb_fargate.stacks import LBFargateStack
from aws_cdk_lb_fargate.config import Config


class AwsCdkLbFargateStack(LBFargateStack[Config]):
    @property
    def _base_name(self) -> str:
        return self.construct_id

    def _name(self, suffix: str = "", prefix: str = "") -> str:
        return "".join(
            [
                part[0].upper() + part[1:]
                for part in f"{prefix} {self._base_name} {suffix}".split()
            ]
        )

    def __init__(
        self,
        scope: Construct,
        config: Config,
        **kwargs,
    ) -> None:
        self.construct_id = f"{config.env.capitalize()}AwsCdkLbFargateStack"

        super().__init__(scope, self.construct_id, **kwargs)

        # Assume a VPC is already created or available
        vpc = ec2.Vpc.from_lookup(
            self, self._name("VPC"), vpc_id=config.vpc_id
        )

        fargate = self.fargate(config, vpc)

        CfnOutput(
            self,
            self._name("LoadBalancerDNS"),
            value=fargate.load_balancer.load_balancer_dns_name,
        )
