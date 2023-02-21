import math
import random

from data import Data
from modes.mode_base import FrameBounds, ModeBase


class Mode(ModeBase):
    @classmethod
    def get_frame_bounds(cls, data: Data) -> FrameBounds:
        if data.frame_index == 0:
            return FrameBounds(width=data.width, height=data.height)
        else:
            return FrameBounds(
                width=math.floor(random.random() * data.width),
                height=math.floor(random.random() * data.height),
            )
