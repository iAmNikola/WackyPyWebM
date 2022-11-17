from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Tuple


@dataclass
class SplitInfo:
    video_path: Path
    width: int
    height: int
    num_frames: int
    fps: float
    keyframe_file: Path


@dataclass
class BaseInfo:
    width: int
    height: int
    num_frames: int
    fps: float
    tempo: float
    angle: float
    transparency: int


class ModeBase(ABC):
    def setup():
        pass

    @abstractmethod
    def get_frame_bounds() -> Tuple[int, int]:
        pass
