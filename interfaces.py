from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict


@dataclass
class SetupInfo:
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

    def extend(self, frame_index: int, frame_path: Path):
        return Info(
            self.width,
            self.height,
            self.num_frames,
            self.fps,
            self.tempo,
            self.angle,
            self.transparency,
            frame_index,
            frame_path,
        )


@dataclass
class Info(BaseInfo):
    frame_index: int
    frame_path: Path


class ModeBase(ABC):
    @classmethod
    def setup(cls, setup_info: SetupInfo):
        pass

    @abstractmethod
    def get_frame_bounds(info: Info) -> Dict[str, Any]:
        pass
