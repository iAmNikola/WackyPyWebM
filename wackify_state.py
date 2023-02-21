import math
from functools import reduce
from pathlib import Path
from typing import Dict, List, Tuple, Union

from data import Data
from modes.mode_base import FrameBounds, ModeBase
from util.tmp_paths import TmpPaths


class WackifyState:
    def __init__(self, modes: Dict[str, ModeBase], selected_modes: List[str]) -> None:
        self.modes = modes
        self.selected_modes = selected_modes
        self.width: int = None
        self.height: int = None
        self.fps: str = None
        self.num_frames: int = None
        self.delta: int = None
        self.same_size_count: int = 0
        self.fssb_i: int = 0
        self.frame_size_smoothing_buffer: List[Tuple[int, int]] = None
        self.tmp_webm_files = []
        self.has_audio: bool = None
        self.frame_bounds: FrameBounds = None
        self.prev_frame: FrameBounds = None

    def generate_smoothing_buffer(self, smoothing_lvl):
        self.frame_size_smoothing_buffer = [(self.width, self.height) for _ in range(smoothing_lvl)]

    def update_prev_frame(self):
        self.prev_frame = FrameBounds.copy(self.frame_bounds)

    def apply_frame_bounds_from_selected_modes(self, data: Data):
        for mode in self.selected_modes:
            new_frame_bounds = self.modes[mode].get_frame_bounds(data)
            if new_frame_bounds.width is not None:
                self.frame_bounds.width = new_frame_bounds.width
            if new_frame_bounds.height is not None:
                self.frame_bounds.height = new_frame_bounds.height
            if new_frame_bounds.vf_command is not None:
                self.frame_bounds.vf_command = new_frame_bounds.vf_command

        self.frame_bounds.width = max(min(self.frame_bounds.width, self.width), self.delta)
        self.frame_bounds.height = max(min(self.frame_bounds.height, self.height), self.delta)

    def apply_smoothing(self, smoothing: int):
        self.frame_size_smoothing_buffer[self.fssb_i] = [self.frame_bounds.width, self.frame_bounds.height]
        self.fssb_i = (self.fssb_i + 1) % smoothing

        self.frame_bounds.width = reduce(lambda s, e: s + e[0], self.frame_size_smoothing_buffer, 0) // smoothing
        self.frame_bounds.height = reduce(lambda s, e: s + e[1], self.frame_size_smoothing_buffer, 0) // smoothing

    def generate_ffmpeg_command(self, frame_i: int, frame_path: Path, bitrate: Union[str, int], num_threads: int):
        # fmt:off
        command = [
            'ffmpeg', '-y', '-r', self.fps,
            '-start_number', str(frame_i - self.same_size_count),
            '-i', TmpPaths.tmp_frame_files,
            '-frames:v', str(self.same_size_count) if frame_i != self.num_frames else '1',
            '-c:v', 'vp8', '-b:v', str(bitrate),
            '-crf', '10', '-vf',
        ]
        # fmt:on
        vf_command = self.frame_bounds.vf_command
        if vf_command is None:
            if frame_i != self.num_frames:
                # fmt:off
                vf_command = [
                    f'scale={self.prev_frame.width}x{self.prev_frame.height}',
                    '-aspect', f'{self.prev_frame.width}:{self.prev_frame.height}',
                ]
                # fmt:on
            else:
                # fmt:off
                vf_command = [
                    f'scale={self.frame_bounds.width}x{self.frame_bounds.height}',
                    '-aspect', f'{self.frame_bounds.width}:{self.frame_bounds.height}',
                ]
                # fmt:on

        section_path = TmpPaths.tmp_resized_frames / (
            f'{frame_path.stem}.webm' if frame_i != self.num_frames else 'end.webm'
        )
        # fmt:off
        command += vf_command + [
            '-threads',
            str(min(num_threads, math.ceil(self.same_size_count / 10))) if frame_i != self.num_frames else '1',
            '-f', 'webm', '-auto-alt-ref', '0',
            section_path,
        ]
        # fmt:on
        return command, section_path

    @property
    def sum_of_abs_diff_width_n_height(self):
        return abs(self.frame_bounds.width - self.prev_frame.width) + abs(
            self.frame_bounds.height - self.prev_frame.height
        )
