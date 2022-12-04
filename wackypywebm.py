import math
import shutil
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Dict, List, Tuple

from natsort import natsorted

import ffmpeg_util
from args_util import PARSER
from data import BaseData, SetupData
from localization import localize_str, set_locale
from modes.mode_base import ModeBase
from util import (
    TMP_PATHS,
    build_tmp_paths,
    find_min_non_error_size,
    fix_terminal,
    get_valid_path,
    load_modes,
    parse_fps,
)

MODES: Dict[str, ModeBase] = load_modes()
_SELECTED_MODES: List[str] = []


def parse_arguments(args: Dict[str, Any]):
    for key, value in args.items():
        if key == 'keyframes' and isinstance(args[key], str):
            args[key] = Path(value).resolve()
            if not args[key].is_file():
                print('ERROR')  # TODO: more verbose
                PARSER.print_help()
                exit()
        elif key in ['compression', 'transparency', 'smoothing', 'threads']:
            args[key] = int(value)
        elif key in ['angle', 'tempo']:
            args[key] = float(value)


def print_config(selected_modes: List[str], args: Dict[str, Any], video_info: Tuple[Tuple[int, int], str, int, int]):
    _, _, bitrate, _ = video_info
    print(localize_str('config_header'))
    print(localize_str('config_mode_list', args={'modes': [mode.title() for mode in selected_modes]}))
    if 'bounce' in selected_modes or 'shutter' in selected_modes:
        print(localize_str('bounce_speed', args={'tempo': args['tempo']}))
    elif 'rotate' in selected_modes:
        print(localize_str('rotate_speed', args={'angle': args['angle']}))
    elif 'keyframes' in selected_modes:
        print(localize_str('keyframe_file', args={'file', args['keyframes']}))
    if args['bitrate'] != bitrate:
        print(localize_str('output_bitrate', args={'bitrate': bitrate}))
    print(localize_str('config_footer'))


def wackify(selected_modes: List[str], video_path: Path, args: Dict[str, Any], output_path: Path):
    parse_arguments(args)

    video_info = ffmpeg_util.get_video_info(video_path)
    (width, height), fps, bitrate, num_frames = video_info

    if args['bitrate'] is None:
        args['bitrate'] = min(bitrate or 500000, 1000000)

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

    print(localize_str('creating_temp_dirs'))
    build_tmp_paths()

    print(localize_str('splitting_audio'))
    has_audio = splitting_successful = ffmpeg_util.split_audio(video_path)

    print(localize_str('splitting_frames'))
    ffmpeg_util.split_frames(video_path, transparent='transparency' in selected_modes, threads=args['threads'])

    setup_data = SetupData(video_path, width, height, num_frames, parse_fps(fps), args['keyframes'])
    base_data = BaseData(width, height, num_frames, parse_fps(fps), args['tempo'], args['angle'], args['transparency'])

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
    frame_size_smoothing_buffer = [[width, height] for i in range(args['smoothing'])]
    fssb_i = 0
    tmp_frame_files = TMP_PATHS['tmp_frame_files']
    tmp_webm_files = []
    with ThreadPoolExecutor(max_workers=args['threads']) as executor:
        frames_processed = [False] * num_frames
        for i, frame_path in enumerate(natsorted(TMP_PATHS['tmp_frames'].glob('*.png')), start=1):
            data = base_data.extend((i - 1), frame_path)

            frame_bounds = {'width': width, 'height': height}
            for mode in selected_modes:
                new_frame_bounds: Dict = MODES[mode].get_frame_bounds(data)
                for key, value in new_frame_bounds.items():
                    frame_bounds[key] = value

            frame_bounds['width'] = max(min(frame_bounds['width'], width), delta)
            frame_bounds['height'] = max(min(frame_bounds['height'], height), delta)

            if frame_size_smoothing_buffer:
                frame_size_smoothing_buffer[fssb_i] = frame_bounds
                fssb_i = (fssb_i + 1) % args['smoothing']

            if i == 1:
                prev_width, prev_height = frame_bounds['width'], frame_bounds['height']

            if (
                (abs(frame_bounds['width'] - prev_width) + abs(frame_bounds['height'] - prev_height))
                > args['compression']
                or i == num_frames
                or same_size_count > (num_frames // args['threads'])
            ):
                command = [
                    'ffmpeg',
                    '-y',
                    '-r',
                    fps,
                    '-start_number',
                    str(i - same_size_count),
                    '-i',
                    get_valid_path(tmp_frame_files),
                    '-frames:v',
                    str(same_size_count) if i != num_frames else '1',
                    '-c:v',
                    'vp8',
                    '-b:v',
                    str(args['bitrate']),
                    '-crf',
                    '10',
                    '-vf',
                ]
                vf_command = frame_bounds.get('vf_command')
                if vf_command is None:
                    if i != num_frames:
                        vf_command = [f'scale={prev_width}x{prev_height}', '-aspect', f'{prev_width}:{prev_height}']
                    else:
                        curr_width, curr_height = frame_bounds['width'], frame_bounds['height']
                        vf_command = [f'scale={curr_width}x{curr_height}', '-aspect', f'{curr_width}:{curr_height}']

                section_path = TMP_PATHS['tmp_resized_frames'] / (
                    f'{frame_path.stem}.webm' if i != num_frames else 'end.webm'
                )
                command += vf_command + [
                    '-threads',
                    str(min(args['threads'], math.ceil(same_size_count / 10))) if i != num_frames else '1',
                    '-f',
                    'webm',
                    '-auto-alt-ref',
                    '0',
                    get_valid_path(section_path),
                ]
                executor.submit(
                    ffmpeg_util.exec_command, command, extra_data=(frames_processed, i, same_size_count, num_frames)
                )
                tmp_webm_files.append(f'file {section_path}\n')
                same_size_count = 1
                prev_height, prev_height = frame_bounds['width'], frame_bounds['height']
            else:
                same_size_count += 1
    print()  # exit progress bar line
    fix_terminal()

    end_time = time.perf_counter()
    print(localize_str('done_conversion', args={'time': f'{end_time - start_time:.2f}', 'framecount': num_frames}))

    print(localize_str('writing_concat_file'))
    with open(TMP_PATHS['tmp_concat_list'], 'w') as tmp_concat_list:
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
        get_valid_path(TMP_PATHS['tmp_concat_list']),
    ]
    if has_audio:
        concatenate_command += ['-i', get_valid_path(TMP_PATHS['tmp_audio'])]
    concatenate_command += ['-c', 'copy', '-auto-alt-ref', '0', get_valid_path(output_path)]
    ffmpeg_util.exec_command(concatenate_command)

    print(localize_str('done_removing_temp'))
    shutil.rmtree(TMP_PATHS['tmp_folder'])
    print('Wackified:', output_path)


if __name__ == '__main__':
    ARGS = PARSER.parse_args()

    if ARGS.language:
        set_locale(ARGS.language)

    if not ARGS.file.is_file():
        print(localize_str('video_file_not_found', {'file': str(ARGS.file)}))
        PARSER.print_help()
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

    wackify(_SELECTED_MODES, ARGS.file, vars(ARGS), ARGS.output)
