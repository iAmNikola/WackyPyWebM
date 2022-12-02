import math

from interfaces import ModeBase, Info


class Mode(ModeBase):
    @classmethod
    def get_frame_bounds(info: Info):
        if info.frame_index == 0:
            return None, info.height
        else:
            height = math.floor(abs(math.cos((info.frame_index / (info.fps / info.tempo)) * math.pi) * info.height))
            return None, height
