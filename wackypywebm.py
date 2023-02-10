import math
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Dict, List, Tuple

from natsort import natsorted

import args_util
import ffmpeg_util
from data import BaseData, SetupData
from localization import localize_str, set_locale
from modes.mode_base import FrameBounds, ModeBase
from tmp_paths import TmpPaths
from util import find_min_non_error_size, fix_terminal, get_valid_path, load_modes, parse_fps

MODES: Dict[str, ModeBase] = load_modes()


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
    video_info = ffmpeg_util.get_video_info(video_path)
    (width, height), fps, bitrate, num_frames = video_info

    if args.bitrate is None:
        args.bitrate = min(bitrate or 500000, 1000000)

    delta: int = find_min_non_error_size(width, height)
    print(localize_str('info1', args={'delta': delta, 'video': video_path}))

    print(
        localize_str(
            'info2',
            args={
                'w': width,
                'h': height,
                'framerate': fps,
                'decframerate': parse_fps(fps),
                'bitrate': bitrate,
            },
        )
    )

    print_config(selected_modes, args, video_info)

    TmpPaths.build_tmp_paths()
    print(localize_str('creating_temp_dirs', args={'path': TmpPaths.tmp_folder}))

    print(localize_str('splitting_audio'))
    has_audio = splitting_successful = ffmpeg_util.split_audio(video_path)

    print(localize_str('splitting_frames'))
    ffmpeg_util.split_frames(video_path, transparent='transparency' in selected_modes, threads=args.threads)

    setup_data = SetupData(video_path, width, height, num_frames, parse_fps(fps), args.keyframes)
    base_data = BaseData(width, height, num_frames, parse_fps(fps), args.tempo, args.angle, args.transparency)

    for mode in selected_modes:
        try:
            if not has_audio and MODES[mode].frames_audio_levels:
                print(f"ERROR: Mode '{mode.title()}' needs audio!")
                exit()
        except AttributeError:
            pass
        MODES[mode].setup(setup_data)

    start_time = time.perf_counter()
    print(localize_str('starting_conversion'))

    same_size_count = 0
    fssb_i = 0
    frame_size_smoothing_buffer = [[width, height] for i in range(args.smoothing)]
    tmp_webm_files = []
    with ThreadPoolExecutor(max_workers=args.threads) as executor:
        frames_processed = [False] * num_frames
        for i, frame_path in enumerate(natsorted(TmpPaths.tmp_frames.glob('*.png')), start=1):
            data = base_data.extend((i - 1), frame_path)

            frame_bounds = FrameBounds(width=width, height=height)
            for mode in selected_modes:
                new_frame_bounds = MODES[mode].get_frame_bounds(data)
                if new_frame_bounds.width is not None:
                    frame_bounds.width = new_frame_bounds.width
                if new_frame_bounds.height is not None:
                    frame_bounds.height = new_frame_bounds.height
                if new_frame_bounds.vf_command is not None:
                    frame_bounds.vf_command = new_frame_bounds.vf_command

            frame_bounds.width = max(min(frame_bounds.width, width), delta)
            frame_bounds.height = max(min(frame_bounds.height, width), delta)

            if frame_size_smoothing_buffer:
                frame_size_smoothing_buffer[fssb_i] = frame_bounds
                fssb_i = (fssb_i + 1) % args.smoothing

            if i == 1:
                prev_frame = FrameBounds.copy(frame_bounds)

            if (
                (abs(frame_bounds.width - prev_frame.width) + abs(frame_bounds.height - prev_frame.height))
                > args.compression
                or i == num_frames
                or same_size_count > (num_frames // args.threads)
            ):
                command = [
                    'ffmpeg',
                    '-y',
                    '-r',
                    fps,
                    '-start_number',
                    str(i - same_size_count),
                    '-i',
                    TmpPaths.tmp_frame_files,
                    '-frames:v',
                    str(same_size_count) if i != num_frames else '1',
                    '-c:v',
                    'vp8',
                    '-b:v',
                    str(args.bitrate),
                    '-crf',
                    '10',
                    '-vf',
                ]
                vf_command = frame_bounds.vf_command
                if vf_command is None:
                    if i != num_frames:
                        vf_command = [
                            f'scale={prev_frame.width}x{prev_frame.height}',
                            '-aspect',
                            f'{prev_frame.width}:{prev_frame.height}',
                        ]
                    else:
                        vf_command = [
                            f'scale={frame_bounds.width}x{frame_bounds.height}',
                            '-aspect',
                            f'{frame_bounds.width}:{frame_bounds.height}',
                        ]

                section_path = TmpPaths.tmp_resized_frames / (
                    f'{frame_path.stem}.webm' if i != num_frames else 'end.webm'
                )
                command += vf_command + [
                    '-threads',
                    str(min(args.threads, math.ceil(same_size_count / 10))) if i != num_frames else '1',
                    '-f',
                    'webm',
                    '-auto-alt-ref',
                    '0',
                    section_path,
                ]
                executor.submit(
                    ffmpeg_util.exec_command, command, extra_data=(frames_processed, i, same_size_count, num_frames)
                )
                tmp_webm_files.append(f'file {get_valid_path(section_path)}\n')
                same_size_count = 1
                prev_frame = FrameBounds.copy(frame_bounds)
            else:
                same_size_count += 1
    fix_terminal()  # exit progress bar line

    end_time = time.perf_counter()
    print(localize_str('done_conversion', args={'time': f'{end_time - start_time:.2f}', 'framecount': num_frames}))

    print(localize_str('writing_concat_file'))
    with open(TmpPaths.tmp_concat_list, 'w') as tmp_concat_list:
        tmp_concat_list.writelines(tmp_webm_files)

    print(localize_str(f'concatenating{"_audio" if has_audio else ""}'))
    concatenate_command = [
        'ffmpeg',
        '-y',
        '-f',
        'concat',
        '-safe',
        '0',
        '-i',
        TmpPaths.tmp_concat_list,
    ]
    if has_audio:
        concatenate_command += ['-i', TmpPaths.tmp_audio]
    concatenate_command += ['-c', 'copy', '-auto-alt-ref', '0', output_path]
    ffmpeg_util.exec_command(concatenate_command)

    print(localize_str('done_removing_temp'))
    TmpPaths.cleanup()
    print('Wackified:', output_path)


if __name__ == '__main__':
    ARGS = args_util.parse_args()

    if ARGS.language:
        set_locale(ARGS.language)

    if not ARGS.file.is_file():
        print(localize_str('video_file_not_found', {'file': str(ARGS.file)}))
        args_util.print_help()
        exit()
    ARGS.file = ARGS.file.resolve()
    _SELECTED_MODES = [mode.lower() for mode in ARGS.modes.split("+")]
    for SELECTED_MODE in _SELECTED_MODES:
        if SELECTED_MODE not in MODES:
            print(f'Mode "{SELECTED_MODE}" isn\'t available.')
            exit()

    if ARGS.output:
        ARGS.output = ARGS.output.resolve()
        ARGS.output.parent.mkdir(parents=True, exist_ok=True)
    else:
        ARGS.output = ARGS.file.parent / f'{ARGS.file.stem}_{"_".join(_SELECTED_MODES)}.webm'
    try:
        wackify(_SELECTED_MODES, ARGS.file, ARGS, ARGS.output)
    except Exception as exception:
        print(exception)
        print('-' * 20)
        print('Something unexpected happened. Cleaning up...')
        TmpPaths.cleanup()
