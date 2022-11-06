import argparse
import os
from pathlib import Path
from typing import Dict, List

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


def mode_selection():
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

    while True:
        draw()
        if set_selected_mode(get_key_press()):
            if _MODES[_SELECTED_MODE] in ['keyframes', 'angle', 'transparency']:
                _KEYS_TO_FLAGS['x'] = f'{_MODES[_SELECTED_MODE]}'
            elif _MODES[_SELECTED_MODE] in ['bounce', 'shutter']:
                _KEYS_TO_FLAGS['x'] = 'tempo'
            break


_KEYS_TO_FLAGS: Dict[str, str] = {
    'b': 'bitrate',
    't': 'threads',
    'o': 'output',
    'c': 'compression',
    's': 'smoothing',
}
_FLAGS: Dict[str, str] = {}
_FILEPATH: Path = None


def set_options():
    def draw_options():
        util.clear()
        if _MODES[_SELECTED_MODE] == 'keyframes':
            print(colored(f'{localize_str("change_options_k")}\n', attrs=['bold', 'underline']))
        else:
            print(colored(f'{localize_str("change_options")}\n', attrs=['bold', 'underline']))

        for key, flag in _KEYS_TO_FLAGS.items():
            print(f'{key}: {get_arg_desc(flag)}')

        if _FLAGS:
            print(colored(f'\n{localize_str("current_arg_values")}', attrs=['bold', 'underline']))
        for flag, value in _FLAGS.items():
            print(f'--{flag} = "{value}"')

    def draw_arg_input(flag: str):
        util.clear()
        text = localize_str("enter_arg_value", args={'arg': flag})
        print(colored(f'{text}', attrs=['bold', 'underline']))
        if _FLAGS.get(flag):
            print(f'Current value: "{_FLAGS[flag]}"\n')

    def configure_options(key: str):
        if key == KEY_CODES['ENTER']:
            return True
        if key.lower() not in _KEYS_TO_FLAGS:
            return False
        draw_arg_input(_KEYS_TO_FLAGS[key.lower()])
        value = input('Set value: ')
        if value:
            _FLAGS[_KEYS_TO_FLAGS[key]] = value

    def draw_file_input(file_not_found: bool = False):
        util.clear()
        if file_not_found:
            print(colored(localize_str('file_not_found'), attrs=['bold', 'underline']))
        print(colored(localize_str('enter_file_path'), attrs=['bold', 'underline']))

    while True:
        draw_options()
        if configure_options(get_key_press()):
            break

    global _FILEPATH
    draw_file_input()
    while True:
        _FILEPATH = Path(input()).resolve()
        if _FILEPATH.is_file():
            break
        draw_file_input(file_not_found=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--lang', choices=localization.get_locales(), default='en_us')
    args = parser.parse_args()

    localization.set_locale(args.lang)

    mode_selection()
    set_options()
