import math

from data import Data
from modes.mode_base import ModeBase


class Mode(ModeBase):
    @classmethod
    def get_frame_bounds(cls, data: Data):
        if data.frame_index == 0:
            return {'width': data.width}
        else:
            return {
                'width': math.floor(abs(math.cos((data.frame_index / (data.fps / data.tempo)) * math.pi) * data.width))
            }
