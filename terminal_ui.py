import argparse
import os
from pathlib import Path
from typing import Dict, List, Tuple

from termcolor import colored

import localization
import util
import wackypywebm
from args_util import get_arg_desc
from localization import localize_str
from util import KEY_CODES, get_key_press

if os.name == 'nt':
    os.system('color')

_MODES: List = list(wackypywebm.MODES.keys())
_SELECTED_MODE: int = _MODES.index('bounce')


def mode_selection() -> Dict[str, str]:
    def draw():
        util.clear()
        print(colored(f'{localize_str("select_mode_arrows")}\n', attrs=['bold', 'underline']))
        tmp = []
        for mode in _MODES:
            if _MODES[_SELECTED_MODE] == mode:
                tmp.append(colored(mode, attrs=['underline']))
            else:
                tmp.append(mode)
        print('    '.join(tmp))

    def set_selected_mode(key) -> bool:
        global _SELECTED_MODE
        if key == KEY_CODES['ENTER']:
            return True
        if key == KEY_CODES['ARROW_LEFT']:
            if _SELECTED_MODE == 0:
                _SELECTED_MODE = len(_MODES) - 1
            else:
                _SELECTED_MODE -= 1
        if key == KEY_CODES['ARROW_RIGHT']:
            if _SELECTED_MODE == (len(_MODES) - 1):
                _SELECTED_MODE = 0
            else:
                _SELECTED_MODE += 1
        return False

    keys_to_flags: Dict[str, str] = {
        'b': 'bitrate',
        't': 'threads',
        'o': 'output',
        'c': 'compression',
        's': 'smoothing',
    }

    while True:
        draw()
        if set_selected_mode(get_key_press()):
            if _MODES[_SELECTED_MODE] in ['keyframes', 'angle', 'transparency']:
                keys_to_flags['x'] = f'{_MODES[_SELECTED_MODE]}'
            elif _MODES[_SELECTED_MODE] in ['bounce', 'shutter']:
                keys_to_flags['x'] = 'tempo'
            return keys_to_flags


def set_options(keys_to_flags: Dict[str, str]) -> Tuple[Dict[str, str], Path]:
    flags: Dict[str, str] = {}
    filepath: Path = None

    def draw_options():
        util.clear()
        if _MODES[_SELECTED_MODE] == 'keyframes':
            print(colored(f'{localize_str("change_options_k")}\n', attrs=['bold', 'underline']))
        else:
            print(colored(f'{localize_str("change_options")}\n', attrs=['bold', 'underline']))

        for key, flag in keys_to_flags.items():
            print(f'{key}: {get_arg_desc(flag)}')

        if flags:
            print(colored(f'\n{localize_str("current_arg_values")}', attrs=['bold', 'underline']))
        for flag, value in flags.items():
            print(f'--{flag} = "{value}"')

    def draw_arg_input(flag: str):
        util.clear()
        text = localize_str("enter_arg_value", args={'arg': flag})
        print(colored(f'{text}', attrs=['bold', 'underline']))
        if flags.get(flag):
            print(f'Current value: "{flags[flag]}"\n')

    def configure_options(key: str):
        if key == KEY_CODES['ENTER']:
            return True
        if key.lower() not in keys_to_flags:
            return False
        draw_arg_input(keys_to_flags[key.lower()])
        value = input('Set value: ')
        if value:
            flags[keys_to_flags[key]] = value

    while True:
        draw_options()
        if configure_options(get_key_press()):
            break

    def draw_file_input(file_not_found: bool = False):
        util.clear()
        if file_not_found:
            print(colored(localize_str('file_not_found'), attrs=['bold', 'underline']))
        print(colored(localize_str('enter_file_path'), attrs=['bold', 'underline']))

    draw_file_input()
    while True:
        filepath = Path(input()).resolve()
        if filepath.is_file():
            return flags, filepath
        draw_file_input(file_not_found=True)


def review_options(flags: Dict[str, str], filepath: Path):
    def draw():
        util.clear()
        print(colored(localize_str('review_settings'), attrs=['bold', 'underline']))
        print(colored(localize_str('r_s_mode'), attrs=['underline']), _MODES[_SELECTED_MODE])
        print(colored(localize_str('r_s_args'), attrs=['underline']))
        for key, value in flags.items():
            print(f'    {key}: "{value}"')
        print(colored(localize_str('r_s_file'), attrs=['underline']), filepath)

    draw()
    while True:
        if get_key_press() == KEY_CODES['ENTER']:
            if 'bitrate' not in flags:
                flags['bitrate'] = '1M'
            if 'thread' not in flags:
                flags['thread'] = 2
            if 'tempo' not in flags:
                flags['tempo'] = 2
            if 'angle' not in flags:
                flags['angle'] = 360
            if 'compression' not in flags:
                flags['compression'] = 0
            if 'transparency' not in flags:
                flags['transparency'] = 1
            if 'smoothing' not in flags:
                flags['smoothing'] = 0
            if 'output' not in flags:
                flags['output'] = str(filepath.parent / f'{filepath.stem}_{_MODES[_SELECTED_MODE]}.webm')
            return flags


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--lang', choices=localization.get_locales(), default='en_us')
    args = parser.parse_args()

    localization.set_locale(args.lang)

    keys_to_flags = mode_selection()
    flags, filepath = set_options(keys_to_flags)
    flags = review_options(flags, filepath)
