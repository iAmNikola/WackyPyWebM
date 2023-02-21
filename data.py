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


class Data(BaseData):
    def __init__(self, base_data: BaseData, frame_index: int, frame_path: Path):
        self.width = base_data.width
        self.height = base_data.height
        self.num_frames = base_data.num_frames
        self.fps = base_data.fps
        self.tempo = base_data.tempo
        self.angle = base_data.angle
        self.transparency = base_data.transparency
        self.frame_index = frame_index
        self.frame_path = frame_path
