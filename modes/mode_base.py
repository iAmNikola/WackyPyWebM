from abc import ABC, abstractmethod
from typing import Any, Dict
from data import SetupData, Data


class ModeBase(ABC):
    @classmethod
    def setup(cls, setup_info: SetupData):
        pass

    @abstractmethod
    def get_frame_bounds(info: Data) -> Dict[str, Any]:
        pass
