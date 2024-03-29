import math
from typing import List

import util.ffmpeg_util as ffmpeg_util
from data import Data, SetupData
from modes.mode_base import FrameAudioLevel, FrameBounds, ModeBase


class Mode(ModeBase):
    frames_audio_levels: List[FrameAudioLevel] = []

    @classmethod
    def setup(cls, setup_data: SetupData):
        cls.frames_audio_levels = ffmpeg_util.get_frames_audio_levels(setup_data.video_path)

    @classmethod
    def get_frame_bounds(cls, data: Data) -> FrameBounds:
        if data.frame_index == 0:
            return FrameBounds(height=data.height)

        fal = cls.frames_audio_levels[
            max(
                min(
                    math.floor((data.frame_index / (data.num_frames - 1)) * (len(cls.frames_audio_levels) - 1)),
                    (len(cls.frames_audio_levels) - 1),
                ),
                0,
            )
        ]
        return FrameBounds(height=math.floor(abs(data.height * fal.percent_max)))
