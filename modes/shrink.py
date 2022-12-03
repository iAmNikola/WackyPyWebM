import math

from data import Data
from modes.mode_base import ModeBase


class Mode(ModeBase):
    @classmethod
    def get_frame_bounds(cls, data: Data):
        return {'height': max(1, math.floor(data.height - (data.frame_index / data.num_frames) * data.height))}
