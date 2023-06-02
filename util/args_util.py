import argparse
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Union

from localization import get_locales


class IArgs:
    file: Path
    modes: str
    keyframes: Optional[Path]
    bitrate: Optional[Union[str, int]]
    tempo: float
    angle: float
    output: Optional[Path]
    compression: int
    language: str
    transparency: int
    smoothing: int
    threads: int

    def __init__(self, args: Dict[str, Any]) -> None:
        for key, value in args.items():
            if key == 'keyframes' and isinstance(args[key], str):
                args[key] = Path(value).resolve()
                if not args[key].is_file():
                    print('[ERROR] Incorrect path to keyframe file provided.')
                    print_help()
                    sys.exit(1)
            elif key in ['compression', 'transparency', 'smoothing', 'threads']:
                args[key] = int(value)
            elif key in ['angle', 'tempo']:
                args[key] = float(value)

        self.keyframes = args['keyframes']
        self.bitrate = args['bitrate']
        self.tempo = args['tempo']
        self.angle = args['angle']
        self.output = args['output']
        self.compression = args['compression']
        self.transparency = args['transparency']
        self.smoothing = args['smoothing']
        self.threads = args['threads']
        self.output = args['output']


PARSER = argparse.ArgumentParser()
PARSER.add_argument('file', type=Path, help='Path to file you want to be wacky.')
PARSER.add_argument('modes', type=str, default='bounce', nargs='?', help='Modes to apply to file.')
PARSER.add_argument(
    '-k', '--keyframes', type=Path, help='Only used with "Keyframes" mode; sets the keyframe file to use.'
)
PARSER.add_argument(
    '-b', '--bitrate', type=str, help='Sets the maximum bitrate of the video. Lowering this might reduce file size.'
)
PARSER.add_argument('-t', '--tempo', type=float, default=2, help='Regulates speed of bouncing.')
PARSER.add_argument(
    '-a', '--angle', type=float, default=360, help='Angle to rotate per second when using "Rotate" mode.'
)
PARSER.add_argument('-o', '--output', type=Path, help="Sets output path.")
PARSER.add_argument(
    '-c', '--compression', type=int, default=0, help='Sets compression level. Higher values means more compression.'
)
PARSER.add_argument('-l', '--language', type=str, default='en_us', choices=get_locales(), help='Sets language.')
PARSER.add_argument(
    '--transparency',
    type=int,
    choices=[0, 1],
    default=1,
    help='Sets the transparency threshold for use with the "Transparency" mode.',
)
PARSER.add_argument('-s', '--smoothing', type=int, default=0, help='Sets the level of smoothing to apply.')
PARSER.add_argument('--threads', type=int, default=os.cpu_count() + 4, help='Sets maximum number of threads to use.')


def get_arg_desc(dest):
    for action in PARSER._actions:
        if dest == action.dest:
            return action.help
    return 'NOT_FOUND'


def parse_args(*args) -> IArgs:
    return PARSER.parse_args(*args)


def print_help():
    PARSER.print_help()
