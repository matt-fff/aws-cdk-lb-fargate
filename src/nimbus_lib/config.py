from nimbus_lib.configs import FargateConfig


class Config(FargateConfig):
    # Put custom configuration here.
    pass


config = Config()  # pyright: ignore
__all__ = ["config"]
