from dataclasses import dataclass
from pathlib import Path


@dataclass
class SetupData:
    video_path: Path
    width: int
    height: int
    num_frames: int
    fps: float
    keyframe_file: Path


@dataclass
class BaseData:
    width: int
    height: int
    num_frames: int
    fps: float
    tempo: float
    angle: float
    transparency: int

    def extend(self, frame_index: int, frame_path: Path):
        return Data(
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
class Data(BaseData):
    frame_index: int
    frame_path: Path
