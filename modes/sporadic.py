import math
import random
from data import Data
from modes.mode_base import ModeBase


class Mode(ModeBase):
    @classmethod
    def get_frame_bounds(cls, data: Data):
        if data.frame_index == 0:
            return {'width': data.width, 'height': data.height}
        else:
            return {
                'width': math.floor(random.random() * data.width),
                'height': math.floor(random.random() * data.height),
            }
