from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Union
from data import SetupData, Data


def load_modes():
    modes = {}
    for mode in (Path(__file__).parent.resolve()).glob('*.py'):
        if mode.stem != 'mode_base':
            modes[mode.stem] = __import__(f'modes.{mode.stem}', fromlist=['Mode']).Mode
    return modes


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

    def __str__(self) -> str:
        return (
            f'FrameBounds: {"width="+str(self.width) if self.width else ""}'
            f' {"height="+str(self.height) if self.height else ""}'
            f' {"vf_command="+str(self.vf_command) if self.vf_command else ""}'
        )


@dataclass
class FrameAudioLevel:
    dbs: float
    percent_max: float

    @classmethod
    def from_dict(cls, frame_dbs: Dict[str, Dict[str, Union[str, float]]]):
        return cls(float(frame_dbs['tags']['lavfi.astats.Overall.RMS_level']), None)


class ModeBase(ABC):
    @classmethod
    def setup(cls, setup_data: SetupData):
        pass

    @classmethod
    @abstractmethod
    def get_frame_bounds(cls, data: Data) -> FrameBounds:
        pass
