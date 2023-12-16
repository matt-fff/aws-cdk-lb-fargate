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
TConfig = TypeVar("TConfig", bound=confs.BastionConfig)


class BastionStack(Stack, Nameable, Generic[TConfig]):
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

        user_data = None
        if config.bootstrap_script is not None:
            with open(config.bootstrap_script, "r", encoding="utf-8") as file:
                bootstrap_script = file.read()
            user_data = ec2.UserData.custom(bootstrap_script)

        ec2_security_group = self.security_group(config, vpc)

        # Create an ec2 instance on which to run tailscale
        ec2_instance = ec2.Instance(
            self,
            self._name("EC2Instance"),
            instance_type=ec2.InstanceType("t2.micro"),
            machine_image=ec2.MachineImage.latest_amazon_linux2023(),
            vpc=vpc,
            vpc_subnets={"subnet_type": ec2.SubnetType.PUBLIC},
            key_name=config.key_pair_name,
            user_data=user_data,
            security_group=ec2_security_group,
        )

        if ec2_instance.node.default_child is None:
            raise ValueError("missing default child for EC2 instance")

        ec2_instance.node.default_child.add_property_override(  # type: ignore
            "SourceDestCheck", False
        )

        CfnOutput(
            self,
            self._name("EC2InstancePublicDNS"),
            value=ec2_instance.instance_public_dns_name,
        )
        CfnOutput(
            self,
            self._name("EC2InstanceID"),
            value=ec2_instance.instance_id,
        )

    def security_group(
        self, config: TConfig, vpc: ec2.IVpc
    ) -> ec2.SecurityGroup:
        sec_group = ec2.SecurityGroup(
            self,
            self._name("FargateIngressSecGrp"),
            vpc=vpc,
            description="Security group to manage bastion host connections",
        )

        # Setup incoming access
        for ip_address in config.ip_allowlist:
            sec_group.add_ingress_rule(
                ec2.Peer.ipv4(
                    ip_address if "/" in ip_address else f"{ip_address}/32"
                ),
                ec2.Port.tcp(config.ssh_port),
                "IP access from allowlist",
            )

        # Give the bastion host access to all of the ingress configurations
        for idx, ingress in enumerate(config.ingress_confs):
            conf_security_group = ec2.SecurityGroup.from_security_group_id(
                self,
                self._name(f"IngressSecGrp{idx}"),
                security_group_id=ingress.security_group_id,
            )
            conf_security_group.add_ingress_rule(
                sec_group,
                ec2.Port.tcp(ingress.port),
            )

        return sec_group
