from typing import Generic, TypeVar
from constructs import Construct
from aws_cdk import (
    CfnOutput,
    Stack,
    aws_rds as rds,
    aws_ec2 as ec2,
)
from nimbus_lib import config as confs
from .nameable import Nameable

# pylint: disable=invalid-name
TConfig = TypeVar("TConfig", bound=confs.RdsConfig)


class RdsStack(Stack, Nameable, Generic[TConfig]):
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

        vpc = ec2.Vpc.from_lookup(
            self,
            self._name("VPC"),
            vpc_id=config.vpc_id,
        )

        instance_type = ec2.InstanceType.of(
            config.instance_type.type_, config.instance_type.size
        )

        # Create a new security group
        rds_security_group = ec2.SecurityGroup(
            self,
            self._name("RDSSecurityGroup"),
            vpc=vpc,
            description=(
                "RDS Security Group to allow connections from other subnets"
            ),
        )

        rds_instance = rds.DatabaseInstance(
            self,
            self._name("RDSInstance"),
            database_name=config.database_name,
            engine=rds.DatabaseInstanceEngine.postgres(
                version=config.engine_version
            ),
            instance_type=instance_type,
            vpc_subnets={"subnet_type": config.subnet_type},
            vpc=vpc,
            port=config.db_port,
            removal_policy=config.removal_policy,
            deletion_protection=config.deletion_protection,
            allocated_storage=config.allocated_storage,
            security_groups=[rds_security_group],
        )

        # Associate the secret with the RDS instance
        rds_instance.add_rotation_single_user()

        CfnOutput(
            self,
            self._name("RDSInstanceARN"),
            value=rds_instance.instance_arn,
            description="The ARN of the RDS instance",
        )

        CfnOutput(
            self,
            self._name("RDSInstanceEndpoint"),
            value=rds_instance.db_instance_endpoint_address,
            description="The endpoint address of the RDS instance",
        )

        CfnOutput(
            self,
            self._name("RDSSecurityGroupID"),
            value=rds_security_group.security_group_id,
            description="The ID of the RDS instance's security group",
        )
