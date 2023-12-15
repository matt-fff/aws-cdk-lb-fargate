from abc import ABC, ABCMeta, abstractmethod
from jsii import JSIIMeta


class AbcJsiiMeta(ABCMeta, JSIIMeta):
    pass


class Nameable(ABC, metaclass=AbcJsiiMeta):
    @property
    @abstractmethod
    def _base_name(self) -> str:
        pass

    def _name(self, suffix: str = "", prefix: str = "") -> str:
        return "".join(
            [
                part[0].upper() + part[1:]
                for part in f"{prefix} {self._base_name} {suffix}".split()
            ]
        )
