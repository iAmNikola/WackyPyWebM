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
    args = PARSER.parse_args()

    if args.language:
        set_locale(args.language)

    if not args.file.is_file():
        print(localize_str('video_file_not_found',  { 'file': str(args.file) }))
        PARSER.print_help()
        exit()

    _SELECTED_MODES = [mode.lower() for mode in args.modes.split('+')]
    for selected_mode in _SELECTED_MODES:
        if selected_mode not in MODES:
            print(f'Mode "{selected_mode}" isn\'t available.')
            exit()

    if args.output:
        args.output = args.output.resolve()
        args.output.parent.mkdir(parents=True, exist_ok=True)
    else:
        args.output = args.file.parent / f'{args.file.stem}_{"_".join(_SELECTED_MODES)}.webm'
    
    