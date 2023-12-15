import os
from typing import Iterable

from aws_cdk import RemovalPolicy, aws_rds as rds, aws_ec2 as ec2
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from . import components as comps

SETTINGS_CONFIG = SettingsConfigDict(
    case_sensitive=False,
    env_file=os.environ.get("ENVFILE", ".env"),
    env_file_encoding="utf-8",
    env_nested_delimiter="__",
)


class StackConfig(BaseSettings):
    stack_name: str
    env: str
    account: str
    region: str

    model_config = SETTINGS_CONFIG

    @property
    def construct_id(self) -> str:
        return f"{self.env.capitalize()}{self.stack_name}"


class VpcConfig(StackConfig):
    max_azs: int = 3
    subnets: list[comps.SubnetConfig] = Field(
        default_factory=comps.SubnetConfig.vpc_defaults
    )


class RdsConfig(StackConfig):
    vpc_id: str
    db_port: int = 5432
    allocated_storage: int = 32
    database_name: str = "main"
    instance_type: comps.Ec2Config = Field(
        default=comps.Ec2Config(
            size=ec2.InstanceSize.MICRO, type_=ec2.InstanceClass.T4G
        )
    )
    # TODO support non-postgres
    engine_version: rds.PostgresEngineVersion = (
        rds.PostgresEngineVersion.VER_15_3
    )
    removal_policy: RemovalPolicy = Field(default=RemovalPolicy.SNAPSHOT)
    deletion_protection: bool = Field(default=False)
    subnet_type: ec2.SubnetType = Field(
        default=ec2.SubnetType.PRIVATE_ISOLATED
    )


class FargateConfig(StackConfig):
    vpc_id: str
    container: comps.ContainerConfig
    public_access: bool = False
    scaling: comps.ScalingConfig = comps.ScalingConfig()
    ip_allowlist: list[str] = Field(default_factory=list)
    ingress_confs: list[comps.IngressConfig] = Field(default_factory=list)
    domains: list[comps.DomainConfig] = Field(default_factory=list)

    external_http_port: int = 80
    external_https_port: int = 443

    @property
    def use_efs(self) -> bool:
        return len(self.container.volumes) > 0

    @property
    def supports_https(self) -> bool:
        return any(self.domains)

    @property
    def external_ports(self) -> Iterable[int]:
        if self.supports_https:
            return (self.external_http_port, self.external_https_port)
        return (self.external_http_port,)
