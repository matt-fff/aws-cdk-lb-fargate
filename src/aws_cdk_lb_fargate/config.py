from aws_cdk_lb_fargate.configs import LBFargateConfig


class Config(LBFargateConfig):
    # Put custom configuration here.
    pass


config = Config()  # pyright: ignore
__all__ = ["config"]
