from aws_cdk_lb_fargate.configs import LBFargateConfig


class Config(LBFargateConfig):
    pass


config = Config()  # pyright: ignore
__all__ = ["config"]
