import time
from pathlib import Path
from typing import Any, Dict, List, Tuple

from natsort import natsorted

from args_util import PARSER
from ffmpeg_util import get_video_info, parse_fps, split_audio, split_frames
from interfaces import BaseInfo, ModeBase, SetupInfo
from localization import localize_str, set_locale
from util import TMP_PATHS, build_tmp_paths, find_min_non_error_size, load_modes

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


def print_config(args: Dict[str, Any], video_info: Tuple[Tuple[int, int], str, int, int]):
    _, _, bitrate, _ = video_info
    print(localize_str('config_header'))
    print(localize_str('config_mode_list', args={'modes': [mode.title() for mode in _SELECTED_MODES]}))
    if 'bounce' in _SELECTED_MODES or 'shutter' in _SELECTED_MODES:
        print(localize_str('bounce_speed', args={'tempo': args['tempo']}))
    elif 'rotate' in _SELECTED_MODES:
        print(localize_str('rotate_speed', args={'angle': args['angle']}))
    elif 'keyframes' in _SELECTED_MODES:
        print(localize_str('keyframe_file', args={'file', args['keyframes']}))
    if args['bitrate'] == bitrate:
        print(localize_str('output_bitrate', args={'bitrate': bitrate}))
    print(localize_str('config_footer'))


def wackify(selected_modes: List[str], video_path: Path, args: Dict[str, Any], output_path: Path):
    parse_arguments(args)

    video_info = get_video_info(video_path)
    (width, height), fps, bitrate, num_frames = video_info

    if args['bitrate'] is None:
        args['bitrate'] = min(bitrate or 500000, 1000000)

    delta: int = find_min_non_error_size(width, height)
    print(localize_str('info', args={'delta': delta, 'video': video_path}))

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

    print_config(args, video_info)

    print(localize_str('creating_temp_dirs'))
    build_tmp_paths()

    print(localize_str('splitting_audio'))
    has_audio = splitting_successful = split_audio(video_path)

    print(localize_str('splitting_frames'))
    split_frames(video_path, transparent='transparency' in selected_modes, threads=args['threads'])

    setup_info = SetupInfo(video_path, width, height, num_frames, parse_fps(fps), args['keyframes'])
    base_info = BaseInfo(width, height, num_frames, parse_fps(fps), args['tempo'], args['agnle'], args['transparency'])

    for mode in selected_modes:
        MODES[mode].setup(setup_info)

    start_time = time.perf_counter()
    print(localize_str('starting_conversion'))

    frame_size_smoothing_buffer = [[width, height] for i in range(args['smoothing'])]
    fssb_i = 0

    for i, frame_path in enumerate(natsorted(TMP_PATHS['tmp_frames'].glob('*.png'))):
        info = base_info.extend(i, frame_path)

        frame_bounds = [width, height]
        for mode in selected_modes:
            frame_width, frame_height = MODES[mode].get_frame_bounds(info)
            frame_bounds[0] = frame_width or frame_bounds[0]
            frame_bounds[1] = frame_height or frame_bounds[1]

        if frame_size_smoothing_buffer:
            frame_size_smoothing_buffer[fssb_i] = frame_bounds
            fssb_i = (fssb_i + 1) % args['smoothing']

    end_time = time.perf_counter()


if __name__ == '__main__':
    ARGS = PARSER.parse_args(['/home/wd-nikolad/work/scripts/out.mp4'])

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
