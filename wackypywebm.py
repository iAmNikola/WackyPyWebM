from pathlib import Path
from typing import Any, Dict, List, Tuple

from args_util import PARSER
from ffmpeg_util import get_video_info, parse_fps, split_audio, split_frames
from localization import localize_str, set_locale
from util import build_tmp_paths

# TODO: Load modes dynamically
MODES = {
    'audiobounce': None,
    'bounce': None,
    'speed': None,
    'keyframes': None,
}
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

    # TODO: delta and info 1 impl

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
