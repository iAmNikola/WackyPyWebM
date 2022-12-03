import math

from data import Data
from modes.mode_base import ModeBase


class Mode(ModeBase):
    @classmethod
    def get_frame_bounds(cls, info: Data):
        if info.frame_index == 0:
            return {'height': info.height}
        else:
            height = math.floor(abs(math.cos((info.frame_index / (info.fps / info.tempo)) * math.pi) * info.height))
            return {'height': height}
