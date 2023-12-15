from enum import Enum, unique
from aws_cdk import aws_ec2 as ec2

from pydantic import Field
from pydantic_settings import BaseSettings


@unique
class ContainerImageSource(Enum):
    ECR = "ECR"
    REGISTRY = "REGISTRY"


class IngressConfig(BaseSettings):
    security_group_id: str
    port: int


class SecretConfig(BaseSettings):
    name: str
    region: str


class DomainConfig(BaseSettings):
    domain: str
    subdomain: str | None = None
    private_zone: bool = False
    create_zone: bool = True

    @property
    def name(self):
        if not self.subdomain:
            return self.domain

        return f"{self.subdomain}.{self.domain}"


class Ec2Config(BaseSettings):
    size: ec2.InstanceSize
    type_: ec2.InstanceClass


class ScalingConfig(BaseSettings):
    max_task_count: int = 2
    target_cpu_util_pct: float | int = 65


class VolumeConfig(BaseSettings):
    path: str
    filesys_id: str | None = None


class ContainerConfig(BaseSettings):
    port: int
    image: str
    tag: str = "latest"
    source: ContainerImageSource = ContainerImageSource.REGISTRY
    volumes: list[VolumeConfig] = Field(default_factory=list)
    command: str | None = None


class SubnetConfig(BaseSettings):
    name: str
    subnet_type: ec2.SubnetType
    cidr_mask: int = 24

    @classmethod
    def vpc_defaults(cls) -> list["SubnetConfig"]:
        return [
            cls(
                name="Ingress",
                subnet_type=ec2.SubnetType.PUBLIC,
            ),
            cls(
                name="Compute",
                subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
            ),
            cls(
                name="Isolated",
                subnet_type=ec2.SubnetType.PRIVATE_ISOLATED,
            ),
        ]
