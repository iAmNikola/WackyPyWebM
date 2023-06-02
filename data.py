from pathlib import Path
from typing import Optional


class SetupData:
    __slots__ = ('video_path', 'width', 'height', 'num_frames', 'fps', 'keyframe_file')

    def __init__(
        self,
        video_path: Path,
        width: int,
        height: int,
        num_frames: int,
        fps: float,
        keyframe_file: Optional[Path] = None,
    ) -> None:
        self.video_path = video_path
        self.width = width
        self.height = height
        self.num_frames = num_frames
        self.fps = fps
        self.keyframe_file = keyframe_file


class BaseData:
    __slots__ = ('width', 'height', 'num_frames', 'fps', 'tempo', 'angle', 'transparency')

    def __init__(
        self, width: int, height: int, num_frames: int, fps: float, tempo: float, angle: float, transparency: int
    ) -> None:
        self.width = width
        self.height = height
        self.num_frames = num_frames
        self.fps = fps
        self.tempo = tempo
        self.angle = angle
        self.transparency = transparency


class Data(BaseData):
    __slots__ = ('frame_index', 'frame_path')

    def __init__(self, base_data: BaseData, frame_index: int, frame_path: Path) -> None:
        super().__init__(
            base_data.width,
            base_data.height,
            base_data.num_frames,
            base_data.fps,
            base_data.tempo,
            base_data.angle,
            base_data.transparency,
        )
        self.frame_index = frame_index
        self.frame_path = frame_path
