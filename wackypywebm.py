import sys
import time
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from natsort import natsorted

import localization
import util.args_util as args_util
import util.ffmpeg_util as ffmpeg_util
import util.terminal_util as terminal_util
from data import BaseData, Data, SetupData
from modes.mode_base import FrameBounds, ModeBase, load_modes
from util.tmp_paths import TmpPaths
from wackify_state import WackifyState

MODES: Dict[str, ModeBase] = load_modes()


def print_config(
    selected_modes: List[str], args: args_util.IArgs, video_info: Tuple[Tuple[int, int], str, Optional[int], int]
):
    _, _, bitrate, _ = video_info
    localization.print('config_header')
    localization.print('config_mode_list', args={'modes': [mode.title() for mode in selected_modes]})
    if 'bounce' in selected_modes or 'shutter' in selected_modes:
        localization.print('bounce_speed', args={'tempo': args.tempo})
    elif 'rotate' in selected_modes:
        localization.print('rotate_speed', args={'angle': args.angle})
    elif 'keyframes' in selected_modes:
        localization.print('keyframe_file', args={'file': args.keyframes})
    if args.bitrate != bitrate:
        localization.print('output_bitrate', args={'bitrate': bitrate})
    localization.print('config_footer')


def wackify(selected_modes: List[str], video_path: Path, args: args_util.IArgs, output_path: Optional[Path]):
    ws = WackifyState(MODES, selected_modes)

    video_info = ffmpeg_util.get_video_info(video_path)
    (ws.width, ws.height), ws.fps, bitrate, ws.num_frames = video_info

    if args.bitrate is None:
        args.bitrate = min(bitrate or 500_000, 1_000_000)

    ws.delta = ffmpeg_util.find_min_non_error_size(ws.width, ws.height)
    localization.print('info1', args={'delta': ws.delta, 'video': video_path})

    localization.print(
        'info2',
        args={
            'w': ws.width,
            'h': ws.height,
            'framerate': ws.fps,
            'decframerate': ffmpeg_util.parse_fps(ws.fps),
            'bitrate': bitrate,
        },
    )

    print_config(selected_modes, args, video_info)

    TmpPaths.build_tmp_paths()
    localization.print('creating_temp_dirs', args={'path': TmpPaths.tmp_folder})

    localization.print('splitting_audio')
    ws.has_audio = ffmpeg_util.split_audio(video_path)

    localization.print('splitting_frames')
    ffmpeg_util.split_frames(video_path, transparent='transparency' in selected_modes, threads=args.threads)

    setup_data = SetupData(
        video_path, ws.width, ws.height, ws.num_frames, ffmpeg_util.parse_fps(ws.fps), args.keyframes
    )
    base_data = BaseData(
        ws.width, ws.height, ws.num_frames, ffmpeg_util.parse_fps(ws.fps), args.tempo, args.angle, args.transparency
    )

    for mode in selected_modes:
        try:
            if not ws.has_audio and getattr(MODES[mode], 'frames_audio_levels') == []:
                print(f"ERROR: Mode '{mode.title()}' needs audio!")
                sys.exit(1)
        except AttributeError:
            pass
        MODES[mode].setup(setup_data)

    start_time = time.perf_counter()
    localization.print('starting_conversion')

    ws.generate_smoothing_buffer(args.smoothing)

    ws.start_progress_tracking()
    with ThreadPoolExecutor(max_workers=args.threads) as executor:
        for i, frame_path in enumerate(natsorted(TmpPaths.tmp_frames.glob('*.png')), start=1):
            data = Data(base_data, (i - 1), frame_path)

            ws.frame_bounds = FrameBounds(ws.width, ws.height)
            ws.apply_frame_bounds_from_selected_modes(data)

            if args.smoothing:
                ws.apply_smoothing(args.smoothing)

            if i == 1:
                ws.update_prev_frame()

            if (
                ws.sum_of_abs_diff_width_n_height > args.compression
                or i == ws.num_frames
                or ws.same_size_count > (ws.num_frames // args.threads)
            ):
                command, section_path = ws.generate_ffmpeg_command(i, frame_path, args.bitrate, args.threads)
                executor.submit(
                    ffmpeg_util.exec_command,
                    command,
                    callback=partial(ws.update_progress_tracking, i, ws.same_size_count),
                )
                ws.tmp_webm_files.append(f'file {ffmpeg_util.get_valid_path(section_path)}\n')
                ws.same_size_count = 1
                ws.update_prev_frame()
            else:
                ws.same_size_count += 1

    ws.finish_progress_tracking()
    terminal_util.fix_terminal()  # exit progress bar line

    end_time = time.perf_counter()
    localization.print('done_conversion', args={'time': f'{end_time - start_time:.2f}', 'framecount': ws.num_frames})

    localization.print('writing_concat_file')
    with open(TmpPaths.tmp_concat_list, '+w', encoding='utf-8') as tmp_concat_list:
        tmp_concat_list.writelines(ws.tmp_webm_files)

    localization.print(f'concatenating{"_audio" if ws.has_audio else ""}')
    # fmt:off
    concatenate_command = [
        'ffmpeg', '-y', '-f', 'concat',
        '-safe', '0', '-i', TmpPaths.tmp_concat_list,
    ]
    # fmt:on
    if ws.has_audio:
        concatenate_command += ['-i', TmpPaths.tmp_audio]
    concatenate_command += ['-c', 'copy', '-auto-alt-ref', '0', output_path]
    ffmpeg_util.exec_command(concatenate_command)

    localization.print('done_removing_temp')
    TmpPaths.cleanup()
    print('Wackified:', output_path)


if __name__ == '__main__':
    _args = args_util.parse_args()

    if _args.language:
        localization.set_locale(_args.language)

    if not _args.file.is_file():
        localization.print('video_file_not_found', {'file': str(_args.file)})
        args_util.print_help()
        sys.exit(1)
    _args.file = _args.file.resolve()
    _selected_modes = [mode.lower() for mode in _args.modes.split("+")]
    for selected_mode in _selected_modes:
        if selected_mode not in MODES:
            print(f'Mode "{selected_mode}" isn\'t available.')
            sys.exit(1)

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
