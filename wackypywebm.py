from typing import List

from args_util import PARSER
from localization import localize_str, set_locale

MODES = {
    'audiobounce': None,
    'bounce': None,
    'speed': None,
    'keyframes': None,
}
_SELECTED_MODES: List[str] = []


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

