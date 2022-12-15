from abc import ABC, abstractmethod
from typing import Any, Dict
from data import SetupData, Data


class ModeBase(ABC):
    @classmethod
    def setup(cls, setup_data: SetupData):
        pass

    @classmethod
    @abstractmethod
    def get_frame_bounds(cls, data: Data) -> Dict[str, Any]:
        pass
