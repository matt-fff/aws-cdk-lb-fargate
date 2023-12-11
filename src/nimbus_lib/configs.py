import os
from typing import Iterable
from enum import Enum, unique


from pydantic import BaseSettings, BaseModel, Field


@unique
class ContainerImageSource(Enum):
    ECR = "ECR"
    REGISTRY = "REGISTRY"


class IngressConfig(BaseModel):
    security_group_id: str
    port: int


class SecretConfig(BaseModel):
    name: str
    region: str

    class Config:
        min_anystr_length = 1
        error_msg_templates = {
            "value_error.any_str.min_length": "min_length:{limit_value}",
        }


class DomainConfig(BaseModel):
    domain: str
    subdomain: str | None = None
    private_zone: bool = False
    zone_exists: bool = False

    @property
    def name(self):
        if not self.subdomain:
            return self.domain

        return f"{self.subdomain}.{self.domain}"


class ScalingConfig(BaseModel):
    max_task_count: int = 2
    target_cpu_util_pct: float | int = 65


class ContainerConfig(BaseModel):
    port: int
    image: str
    tag: str = "latest"
    source: ContainerImageSource = ContainerImageSource.REGISTRY
    volumes: list[str] = Field(default_factory=list)
    command: str | None = None


class FargateConfig(BaseSettings):
    stack_name: str
    vpc_id: str
    env: str
    account: str
    region: str
    container: ContainerConfig
    public_access: bool = False
    scaling: ScalingConfig = ScalingConfig()
    ip_allowlist: list[str] = Field(default_factory=list)
    ingress_confs: list[IngressConfig] = Field(default_factory=list)
    domains: list[DomainConfig] = Field(default_factory=list)

    external_http_port: int = 80
    external_https_port: int = 443

    @property
    def use_efs(self) -> bool:
        return len(self.container.volumes) > 0

    @property
    def construct_id(self) -> str:
        return f"{self.env.capitalize()}{self.stack_name}"

    @property
    def supports_https(self) -> bool:
        return any(self.domains)

    @property
    def external_ports(self) -> Iterable[int]:
        if self.supports_https:
            return (self.external_http_port, self.external_https_port)
        return (self.external_http_port,)

    class Config:
        case_sensitive = False
        min_anystr_length = 1
        error_msg_templates = {
            "value_error.any_str.min_length": "min_length:{limit_value}",
        }
        env_file = os.environ.get("ENVFILE", ".env")
        env_file_encoding = "utf-8"
        env_nested_delimiter = "__"


__all__ = [
    "ContainerImageSource",
    "DomainConfig",
    "ScalingConfig",
    "ContainerConfig",
    "FargateConfig",
    "SecretConfig",
    "IngressConfig",
]
