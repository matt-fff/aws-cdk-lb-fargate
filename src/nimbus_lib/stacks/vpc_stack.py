from typing import Generic, TypeVar
from constructs import Construct
from aws_cdk import (
    CfnOutput,
    Stack,
    aws_ec2 as ec2,
)
from nimbus_lib import config as confs
from .nameable import Nameable

# pylint: disable=invalid-name
TConfig = TypeVar("TConfig", bound=confs.VpcConfig)


class VpcStack(Stack, Nameable, Generic[TConfig]):
    @property
    def _base_name(self) -> str:
        return self.construct_id

    def __init__(
        self,
        scope: Construct,
        config: TConfig,
        **kwargs,
    ) -> None:
        self.construct_id = config.construct_id
        super().__init__(scope, self.construct_id, **kwargs)
        subnets = self.subnets(config.subnets)
        self.vpc = ec2.Vpc(
            self,
            self._name("VPC"),
            subnet_configuration=subnets,
            max_azs=config.max_azs,
        )

        CfnOutput(
            self,
            self._name("VpcArn"),
            value=self.vpc.vpc_arn,
            description="The ARN of the virtual private cloud",
        )

        CfnOutput(
            self,
            self._name("VpcId"),
            value=self.vpc.vpc_id,
            description="The ID of the virtual private cloud",
        )

    def subnets(
        self, configs: list[confs.SubnetConfig]
    ) -> list[ec2.SubnetConfiguration]:
        subnets = []
        for config in configs:
            subnets.append(
                ec2.SubnetConfiguration(
                    name=config.name,
                    subnet_type=config.subnet_type,
                    cidr_mask=config.cidr_mask,
                )
            )
        return subnets
