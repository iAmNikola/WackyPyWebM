import math

from data import Data
from modes.mode_base import ModeBase, FrameBounds


class Mode(ModeBase):
    @classmethod
    def get_frame_bounds(cls, data: Data) -> FrameBounds:
        return FrameBounds(height=max(1, math.floor(data.height - (data.frame_index / data.num_frames) * data.height)))
