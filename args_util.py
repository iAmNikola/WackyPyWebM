import argparse
from pathlib import Path
from localization import get_locales


# TODO: check if types of arguments are valid, transparency 1 or 0 thing too
PARSER = argparse.ArgumentParser()
PARSER.add_argument('file', type=Path, help='Path to file you want to be wacky.')
PARSER.add_argument('modes', type=str, default='bounce', nargs='?', help='Modes to apply to file.')
PARSER.add_argument(
    '-k', '--keyframes', type=Path, help='Only used with "Keyframes" mode; sets the keyframe file to use.'
)
PARSER.add_argument(
    '-b', '--bitrate', type=str, help='Sets the maximum bitrate of the video. Lowering this might reduce file size.'
)
PARSER.add_argument('-t', '--tempo', type=int, default=2, help='Regulates speed of bouncing.')
PARSER.add_argument('-a', '--angle', type=int, default=360, help='Angle to rotate per second when using "Rotate" mode.')
PARSER.add_argument('-o', '--output', type=Path, help="Sets output path.")
PARSER.add_argument(
    '-c', '--compression', type=int, default=0, help='Sets compression level. Higher values means more compression.'
)
PARSER.add_argument('-l', '--language', type=str, choices=get_locales(), help='Sets language.')
PARSER.add_argument(
    '--transparency',
    type=float,
    default=1,
    help='Sets the transparency threshold for use with the "Transparency" mode.',
)
PARSER.add_argument('-s', '--smoothing', type=int, default=0, help='Sets the level of smoothing to apply.')
PARSER.add_argument('--threads', help='Sets maximum number of threads to use.')

# TODO: I will see if I implement this functionality
PARSER.add_argument('--no-update-check', action='store_true', help='Disables the automatic update check.')


def get_arg_desc(dest):
    for action in PARSER._actions:
        if dest == action.dest:
            return action.help
    return 'NOT_FOUND'
