import math
import time
from concurrent.futures import ThreadPoolExecutor
from functools import reduce
from pathlib import Path
from typing import Dict, List, Tuple, Union

from natsort import natsorted

import args_util
import ffmpeg_util
from data import BaseData, Data, SetupData
from localization import localize_str, set_locale
from modes.mode_base import FrameBounds, ModeBase
from tmp_paths import TmpPaths
from util import find_min_non_error_size, fix_terminal, get_valid_path, load_modes, parse_fps

MODES: Dict[str, ModeBase] = load_modes()


class WackifyData:
    def __init__(self) -> None:
        self.width: int = None
        self.height: int = None
        self.fps: str = None
        self.num_frames: int = None
        self.delta: int = None
        self.same_size_count: int = 0
        self.fssb_i: int = 0
        self.frame_size_smoothing_buffer: List[Tuple[int, int]] = None
        self.tmp_webm_files = []
        self.has_audio: bool = None
        self.frame_bounds: FrameBounds = None
        self.prev_frame: FrameBounds = None

    def generate_smoothing_buffer(self, smoothing_lvl):
        self.frame_size_smoothing_buffer = [(self.width, self.height) for _ in range(smoothing_lvl)]

    def update_prev_frame(self):
        self.prev_frame = FrameBounds.copy(self.frame_bounds)

    def apply_frame_bounds_from_selected_modes(self, selected_modes: List[str], data: Data):
        for mode in selected_modes:
            new_frame_bounds = MODES[mode].get_frame_bounds(data)
            if new_frame_bounds.width is not None:
                self.frame_bounds.width = new_frame_bounds.width
            if new_frame_bounds.height is not None:
                self.frame_bounds.height = new_frame_bounds.height
            if new_frame_bounds.vf_command is not None:
                self.frame_bounds.vf_command = new_frame_bounds.vf_command

        self.frame_bounds.width = max(min(self.frame_bounds.width, self.width), self.delta)
        self.frame_bounds.height = max(min(self.frame_bounds.height, self.height), self.delta)

    def apply_smoothing(self, smoothing: int):
        self.frame_size_smoothing_buffer[self.fssb_i] = [self.frame_bounds.width, self.frame_bounds.height]
        self.fssb_i = (self.fssb_i + 1) % smoothing

        self.frame_bounds.width = reduce(lambda s, e: s + e[0], self.frame_size_smoothing_buffer, 0) // smoothing
        self.frame_bounds.height = reduce(lambda s, e: s + e[1], self.frame_size_smoothing_buffer, 0) // smoothing

    def generate_ffmpeg_command(self, frame_i: int, frame_path: Path, bitrate: Union[str, int], num_threads: int):
        ...
        # fmt:off
        command = [
            'ffmpeg', '-y', '-r', self.fps,
            '-start_number', str(frame_i - self.same_size_count),
            '-i', TmpPaths.tmp_frame_files,
            '-frames:v', str(self.same_size_count) if frame_i != self.num_frames else '1',
            '-c:v', 'vp8', '-b:v', str(bitrate),
            '-crf', '10', '-vf',
        ]
        # fmt:on
        vf_command = self.frame_bounds.vf_command
        if vf_command is None:
            if frame_i != self.num_frames:
                # fmt:off
                vf_command = [
                    f'scale={self.prev_frame.width}x{self.prev_frame.height}',
                    '-aspect', f'{self.prev_frame.width}:{self.prev_frame.height}',
                ]
                # fmt:on
            else:
                # fmt:off
                vf_command = [
                    f'scale={self.frame_bounds.width}x{self.frame_bounds.height}',
                    '-aspect', f'{self.frame_bounds.width}:{self.frame_bounds.height}',
                ]
                # fmt:on

        section_path = TmpPaths.tmp_resized_frames / (
            f'{frame_path.stem}.webm' if frame_i != self.num_frames else 'end.webm'
        )
        # fmt:off
        command += vf_command + [
            '-threads',
            str(min(num_threads, math.ceil(self.same_size_count / 10))) if frame_i != self.num_frames else '1',
            '-f', 'webm', '-auto-alt-ref', '0',
            section_path,
        ]
        # fmt:on
        return command, section_path

    @property
    def sum_of_abs_diff_width_n_height(self):
        return abs(self.frame_bounds.width - self.prev_frame.width) + abs(
            self.frame_bounds.height - self.prev_frame.height
        )


def print_config(selected_modes: List[str], args: args_util.IArgs, video_info: Tuple[Tuple[int, int], str, int, int]):
    _, _, bitrate, _ = video_info
    print(localize_str('config_header'))
    print(localize_str('config_mode_list', args={'modes': [mode.title() for mode in selected_modes]}))
    if 'bounce' in selected_modes or 'shutter' in selected_modes:
        print(localize_str('bounce_speed', args={'tempo': args.tempo}))
    elif 'rotate' in selected_modes:
        print(localize_str('rotate_speed', args={'angle': args.angle}))
    elif 'keyframes' in selected_modes:
        print(localize_str('keyframe_file', args={'file': args.keyframes}))
    if args.bitrate != bitrate:
        print(localize_str('output_bitrate', args={'bitrate': bitrate}))
    print(localize_str('config_footer'))


def wackify(selected_modes: List[str], video_path: Path, args: args_util.IArgs, output_path: Path):
    wd = WackifyData()

    video_info = ffmpeg_util.get_video_info(video_path)
    (wd.width, wd.height), wd.fps, bitrate, wd.num_frames = video_info

    if args.bitrate is None:
        args.bitrate = min(bitrate or 500000, 1000000)

    wd.delta: int = find_min_non_error_size(wd.width, wd.height)
    print(localize_str('info1', args={'delta': wd.delta, 'video': video_path}))

    print(
        localize_str(
            'info2',
            args={
                'w': wd.width,
                'h': wd.height,
                'framerate': wd.fps,
                'decframerate': parse_fps(wd.fps),
                'bitrate': bitrate,
            },
        )
    )

    print_config(selected_modes, args, video_info)

    TmpPaths.build_tmp_paths()
    print(localize_str('creating_temp_dirs', args={'path': TmpPaths.tmp_folder}))

    print(localize_str('splitting_audio'))
    wd.has_audio = ffmpeg_util.split_audio(video_path)

    print(localize_str('splitting_frames'))
    ffmpeg_util.split_frames(video_path, transparent='transparency' in selected_modes, threads=args.threads)

    setup_data = SetupData(video_path, wd.width, wd.height, wd.num_frames, parse_fps(wd.fps), args.keyframes)
    base_data = BaseData(
        wd.width, wd.height, wd.num_frames, parse_fps(wd.fps), args.tempo, args.angle, args.transparency
    )

    for mode in selected_modes:
        try:
            if not wd.has_audio and MODES[mode].frames_audio_levels:
                print(f"ERROR: Mode '{mode.title()}' needs audio!")
                exit()
        except AttributeError:
            pass
        MODES[mode].setup(setup_data)

    start_time = time.perf_counter()
    print(localize_str('starting_conversion'))

    wd.generate_smoothing_buffer(args.smoothing)
    frames_processed = [False] * wd.num_frames
    with ThreadPoolExecutor(max_workers=args.threads) as executor:
        for i, frame_path in enumerate(natsorted(TmpPaths.tmp_frames.glob('*.png')), start=1):
            data = base_data.extend((i - 1), frame_path)

            wd.frame_bounds = FrameBounds(wd.width, wd.height)
            wd.apply_frame_bounds_from_selected_modes(selected_modes, data)

            if args.smoothing:
                wd.apply_smoothing(args.smoothing)

            if i == 1:
                wd.update_prev_frame()

            if (
                wd.sum_of_abs_diff_width_n_height > args.compression
                or i == wd.num_frames
                or wd.same_size_count > (wd.num_frames // args.threads)
            ):
                command, section_path = wd.generate_ffmpeg_command(i, frame_path, args.bitrate, args.threads)
                executor.submit(
                    ffmpeg_util.exec_command,
                    command,
                    extra_data=(frames_processed, i, wd.same_size_count, wd.num_frames),
                )
                wd.tmp_webm_files.append(f'file {get_valid_path(section_path)}\n')
                wd.same_size_count = 1
                wd.update_prev_frame()
            else:
                wd.same_size_count += 1

    fix_terminal()  # exit progress bar line

    end_time = time.perf_counter()
    print(localize_str('done_conversion', args={'time': f'{end_time - start_time:.2f}', 'framecount': wd.num_frames}))

    print(localize_str('writing_concat_file'))
    with open(TmpPaths.tmp_concat_list, 'w') as tmp_concat_list:
        tmp_concat_list.writelines(wd.tmp_webm_files)

    print(localize_str(f'concatenating{"_audio" if wd.has_audio else ""}'))
    # fmt:off
    concatenate_command = [
        'ffmpeg', '-y', '-f', 'concat',
        '-safe', '0', '-i', TmpPaths.tmp_concat_list,
    ]
    # fmt:on
    if wd.has_audio:
        concatenate_command += ['-i', TmpPaths.tmp_audio]
    concatenate_command += ['-c', 'copy', '-auto-alt-ref', '0', output_path]
    ffmpeg_util.exec_command(concatenate_command)

    print(localize_str('done_removing_temp'))
    TmpPaths.cleanup()
    print('Wackified:', output_path)


if __name__ == '__main__':
    _args = args_util.parse_args()

    if _args.language:
        set_locale(_args.language)

    if not _args.file.is_file():
        print(localize_str('video_file_not_found', {'file': str(_args.file)}))
        args_util.print_help()
        exit()
    _args.file = _args.file.resolve()
    _selected_modes = [mode.lower() for mode in _args.modes.split("+")]
    for selected_mode in _selected_modes:
        if selected_mode not in MODES:
            print(f'Mode "{selected_mode}" isn\'t available.')
            exit()

    if _args.output:
        _args.output = _args.output.resolve()
        _args.output.parent.mkdir(parents=True, exist_ok=True)
    else:
        _args.output = _args.file.parent / f'{_args.file.stem}_{"_".join(_selected_modes)}.webm'

    try:
        wackify(_selected_modes, _args.file, _args, _args.output)
    except Exception as exception:
        print(exception)
        print('-' * 20)
        print('Something unexpected happened. Cleaning up...')
        TmpPaths.cleanup()
