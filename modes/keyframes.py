import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Callable, Union

import ffmpeg_util
from data import Data, FrameAudioLevel, SetupData
from localization import localize_str
from modes.mode_base import ModeBase, FrameBounds


class NumberOfFieldsInvalidException(Exception):
    ...


class TimeInvalidException(Exception):
    ...


class InterpolationModeNotImplementedException(Exception):
    ...


@dataclass
class KeyframeData:
    time: int
    width: int
    height: int
    interp_mode: str

    def get_shape(self):
        return self.width, self.height


@dataclass
class InterpolationData:
    t: float
    width: int
    height: int
    next_width: int
    next_height: int


class Mode(ModeBase):
    keyframes: List[KeyframeData] = []
    kf_index = 0
    interp_modes: Dict[str, Callable[[str, InterpolationData], FrameBounds]] = {}

    @classmethod
    def interpolation(cls, mode: str, data: InterpolationData, setup=False) -> FrameBounds:
        def linear(data: InterpolationData):
            return FrameBounds(
                width=math.floor(data.width + data.t * (data.next_width - data.width)),
                height=math.floor(data.height + data.t * (data.next_height - data.height)),
            )

        def instant(data: InterpolationData):
            return FrameBounds(width=data.width, height=data.height)

        if setup:
            lcls = dict(locals())  # copy to dict to prevent error
            cls.interp_modes = {k: v for k, v in lcls.items() if callable(v) and k != 'cls'}
            return

        return cls.interp_modes[mode](data)

    @classmethod
    def setup(cls, setup_data: SetupData):
        print(localize_str('parsing_keyframes', args={'file': setup_data.keyframe_file}))
        cls.interpolation(None, None, setup=True)
        cls.parse_keyframe_file(setup_data.keyframe_file, setup_data.fps, setup_data.width, setup_data.height)

    @classmethod
    def get_frame_bounds(cls, data: Data) -> FrameBounds:
        incremented = False
        while cls.kf_index != len(cls.keyframes) - 1 and data.frame_index >= cls.keyframes[cls.kf_index + 1].time:
            if incremented:
                print(localize_str('excess_keyframes', args={'time': cls.keyframes[cls.kf_index + 1].time}))
            cls.kf_index += 1
            incremented = True

        if cls.kf_index == len(cls.keyframes) - 1:
            return FrameBounds(
                width=cls.keyframes[cls.kf_index].width,
                height=cls.keyframes[cls.kf_index].height,
            )

        t = (data.frame_index - cls.keyframes[cls.kf_index].time) / (
            cls.keyframes[cls.kf_index + 1].time - cls.keyframes[cls.kf_index].time
        )
        width, height = cls.keyframes[cls.kf_index].get_shape()
        next_width, next_height = cls.keyframes[cls.kf_index + 1].get_shape()

        return cls.interpolation(
            cls.keyframes[cls.kf_index].interp_mode,
            InterpolationData(t, width, height, next_width, next_height),
        )

    @classmethod
    def parse_keyframe_file(cls, keyframe_file: Path, fps: float, width: int, height: int):
        file_lines = keyframe_file.read_text().splitlines()
        lines: List[List[int, List[str]]] = []
        for i, line in enumerate(file_lines, start=1):
            if not (line == '' or line.startswith('#')):
                lines.append([i, [x.strip().lower() for x in line.split(',')]])

        # validate keyframes
        for prev_kf_index, [line_i, data] in enumerate(lines, start=-1):
            if not (3 <= len(data) <= 4):
                raise NumberOfFieldsInvalidException(
                    localize_str(
                        'not_enough_fields' if len(data) < 3 else 'too_many_fields',
                        args={'line': line_i},
                    )
                )

            time = [int(x) if x.isdecimal() else None for x in re.split('[:.-]', data[0])]
            if not (1 <= len(time) <= 2) or None in time:
                raise TimeInvalidException(
                    localize_str(
                        'invalid_time',
                        args={'line': line_i, 'input': data[0]},
                    )
                )

            parsed_time = math.floor(time[0] * fps)
            if len(time) == 2:
                parsed_time += time[1]
                if time[1] >= fps:
                    print(localize_str('large_frame_specifier', args={'line': line_i}))

            interpolation = 'linear'  # default
            if len(data) == 4 and cls.is_interp_mode_valid(data[3]):
                interpolation = data[3]

            cls.keyframes.append(
                KeyframeData(
                    parsed_time,
                    cls.eval_expression(data[1], prev_kf_index, width),
                    cls.eval_expression(data[2], prev_kf_index, height, side_is_width=False),
                    interpolation,
                )
            )

        if cls.keyframes[0].time != 0:
            cls.keyframes.insert(0, KeyframeData(0, width, height, 'linear'))

    @classmethod
    def is_interp_mode_valid(cls, mode: str):
        if mode not in cls.interp_modes:
            raise InterpolationModeNotImplementedException(
                localize_str("unrecognized_interpolation", args={'mode': mode})
            )
        return True

    @classmethod
    def eval_expression(cls, expression: str, prev_kf_index: int, side: int, side_is_width: bool = True):
        def infix_to_postfix():
            @dataclass
            class Operator:
                precedence: int
                associativity: str

                def is_left_assoc(self):
                    return self.associativity == 'left'

                def is_right_assoc(self):
                    return self.associativity == 'right'

            operators = {
                '/': Operator(precedence=2, associativity='left'),
                '*': Operator(precedence=2, associativity='left'),
                '+': Operator(precedence=1, associativity='left'),
                '-': Operator(precedence=1, associativity='left'),
            }

            postfix: List[Union[str, int]] = []
            operator_stack: List[str] = []
            tokens = [x for x in re.split(r'([+\-*/()])', expression) if x != '']
            for token in tokens:
                if re.search(r'^\d+$', token):
                    postfix.append(int(token))
                elif token in operators:
                    if operator_stack:
                        o1 = token
                        o2 = operator_stack[-1]
                        if (operators[o1].is_left_assoc() and operators[o1].precedence <= operators[o2].precedence) or (
                            operators[o1].is_right_assoc() and operators[o1].precedence < operators[o2].precedence
                        ):
                            postfix.append(operator_stack.pop())
                    operator_stack.append(token)
                elif token == '(':
                    operator_stack.append(token)
                elif token == ')':
                    while operator_stack[-1] != '(':
                        postfix.append(operator_stack.pop())
                    operator_stack.pop()
                else:
                    postfix.append(token.lower())

            while operator_stack:
                postfix.append(operator_stack.pop())
            print(postfix)
            return postfix

        def evaulate_postfix(postfix: List[Union[str, int]]) -> int:
            queue: List[int] = []
            for token in postfix:
                if isinstance(token, int):
                    queue.append(token)
                elif token == '+':
                    queue.append(queue.pop() + queue.pop())
                elif token == '-':
                    queue.append(-queue.pop() + queue.pop())
                elif token == '*':
                    queue.append(queue.pop() * queue.pop())
                elif token == '/':
                    queue.append(queue.pop() / queue.pop())
                elif token.startswith('last'):
                    if token.endswith('width'):
                        queue.append(cls.keyframes[prev_kf_index].width)
                    elif token.endswith('height'):
                        queue.append(cls.keyframes[prev_kf_index].height)
                    elif token == 'last':
                        kf = cls.keyframes[prev_kf_index]
                        queue.append(kf.width if side_is_width else kf.height)
                elif token == 'original':
                    queue.append(side)

            return math.floor(queue[0])

        return evaulate_postfix(infix_to_postfix())
