from abc import ABC, abstractmethod
from typing import Any, Dict
from data import SetupData, Data


class FrameBounds:
    def __init__(self, width: int = None, height: int = None, vf_command: str = None) -> None:
        self.width = width
        self.height = height
        self.vf_command = [vf_command] if vf_command else None

    @classmethod
    def copy(cls, frame_bounds: 'FrameBounds'):
        return cls(
            width=frame_bounds.width,
            height=frame_bounds.height,
        )


class ModeBase(ABC):
    @classmethod
    def setup(cls, setup_data: SetupData):
        pass

    @classmethod
    @abstractmethod
    def get_frame_bounds(cls, data: Data) -> FrameBounds:
        pass
