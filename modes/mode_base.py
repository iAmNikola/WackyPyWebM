from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Optional, Union

from data import Data, SetupData


def load_modes():
    modes = {}
    for mode in Path(__file__).parent.resolve().glob('*.py'):
        if mode.stem != 'mode_base':
            modes[mode.stem] = __import__(f'modes.{mode.stem}', fromlist=['Mode']).Mode
    return modes


class FrameBounds:
    __slots__ = ('width', 'height', 'vf_command')

    def __init__(self, width: int = None, height: int = None, vf_command: Optional[str] = None) -> None:  # type: ignore
        self.width = width
        self.height = height
        self.vf_command = [vf_command] if vf_command else None

    @classmethod
    def copy(cls, frame_bounds: 'FrameBounds'):
        return cls(
            width=frame_bounds.width,
            height=frame_bounds.height,
        )

    def __str__(self) -> str:
        return (
            f'FrameBounds: {"width="+str(self.width) if self.width else ""}'
            f' {"height="+str(self.height) if self.height else ""}'
            f' {"vf_command="+str(self.vf_command) if self.vf_command else ""}'
        )


class FrameAudioLevel:
    __slots__ = ('dbs', 'percent_max')

    def __init__(self, frame_dbs: Dict[str, Dict[str, Union[str, float]]]) -> None:
        self.dbs = float(frame_dbs['tags']['lavfi.astats.Overall.RMS_level'])
        self.percent_max = 0.0


class ModeBase(ABC):
    @classmethod
    def setup(cls, setup_data: SetupData):
        pass

    @classmethod
    @abstractmethod
    def get_frame_bounds(cls, data: Data) -> FrameBounds:
        pass
