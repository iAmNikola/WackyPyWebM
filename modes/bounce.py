import math

from interfaces import ModeBase


class Mode(ModeBase):
    @classmethod
    def get_frame_bounds(**kwargs):
        if kwargs['frame'] == 0:
            return kwargs['height']
        else:
            height = math.floor(
                abs(math.cos((kwargs['frame'] / (kwargs['fps'] / kwargs['tempo'])) * math.pi) * kwargs['height'])
            )
            return None, height
