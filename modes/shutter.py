import math

from data import Data
from modes.mode_base import FrameBounds, ModeBase


class Mode(ModeBase):
    @classmethod
    def get_frame_bounds(cls, data: Data) -> FrameBounds:
        if data.frame_index == 0:
            return FrameBounds(width=data.width)
        else:
            return FrameBounds(
                width=math.floor(abs(math.cos((data.frame_index / (data.fps / data.tempo)) * math.pi) * data.width)),
            )
