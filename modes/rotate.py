import math

from data import Data
from modes.mode_base import ModeBase


class Mode(ModeBase):
    @classmethod
    def get_frame_bounds(cls, data: Data):
        if data.frame_index == 0:
            max_size = math.floor(data.width * abs(math.cos(math.pi / 4)) + data.height * abs(math.cos(math.pi / 4)))
            return {'width': max_size, 'height': max_size}
        else:
            angle = data.frame_index * (data.angle / data.num_frames)
            width = math.floor(max(data.width, data.width * abs(math.cos(angle)) + data.height * abs(math.sin(angle))))
            height = math.floor(
                max(data.height, data.width * abs(math.sin(angle)) + data.height * abs(math.cos(angle)))
            )
            return {
                'width': width,
                'height': height,
                'vf_command': [
                    f'pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,setsar=1,rotate={angle:.2f}:bilinear=0',
                ],
            }
