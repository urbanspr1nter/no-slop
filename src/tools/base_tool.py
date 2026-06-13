from abc import ABC, abstractmethod


class BaseTool(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def invoke(self, **kwargs):
        raise NotImplementedError("Must implement invoke!")

    @abstractmethod
    def _truncate(self, **kwargs) -> dict:
        raise NotImplementedError("Must implement _truncate!")

    @abstractmethod
    def _write_log(self, **kwargs) -> str:
        raise NotImplementedError("Must implement _write_log!")
