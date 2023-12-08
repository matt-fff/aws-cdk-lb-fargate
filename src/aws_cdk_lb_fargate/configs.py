import os
from typing import Iterable


from pydantic import BaseSettings, BaseModel


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
    certificate_arn: str | None = None

    @property
    def name(self):
        if not self.subdomain:
            return self.domain

        return f"{self.subdomain}.{self.domain}"


class ScalingConfig(BaseModel):
    max_task_count: int = 2
    target_cpu_util_pct: float | int = 65


class LBFargateConfig(BaseSettings):
    vpc_id: str
    env: str
    account: str
    region: str
    port: int
    image: str
    image_tag: str = "latest"
    whitelist_ip: str | None = None
    public_access: bool = False
    scaling = ScalingConfig()
    ingress_confs: list[IngressConfig] = []
    domains: list[DomainConfig] = []

    @property
    def certs(self) -> Iterable:
        return (d.certificate_arn for d in self.domains if d)

    @property
    def supports_https(self) -> bool:
        return any(self.certs)

    @property
    def external_ports(self) -> Iterable[int]:
        if self.supports_https:
            return (80, 443)
        return (80,)

    class Config:
        case_sensitive = False
        min_anystr_length = 1
        error_msg_templates = {
            "value_error.any_str.min_length": "min_length:{limit_value}",
        }
        env_file = os.environ.get("ENVFILE", ".env")
        env_file_encoding = "utf-8"
        env_nested_delimiter = "__"


__all__ = ["LBFargateConfig", "SecretConfig", "IngressConfig"]
