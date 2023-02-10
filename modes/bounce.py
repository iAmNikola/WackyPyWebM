import math

from data import Data
from modes.mode_base import ModeBase, FrameBounds


class Mode(ModeBase):
    @classmethod
    def get_frame_bounds(cls, data: Data) -> FrameBounds:
        if data.frame_index == 0:
            return FrameBounds(height=data.height)
        else:
            return FrameBounds(
                height=math.floor(abs(math.cos((data.frame_index / (data.fps / data.tempo)) * math.pi) * data.height)),
            )
