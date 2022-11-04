import argparse
import os
from typing import List

from termcolor import colored

import localization
import util
import wackypywebm
from localization import localize_str
from util import KEY_CODES, get_key_press

if os.name == 'nt':
    os.system('color')

_MODES: List = list(wackypywebm.MODES.keys())
_SELECTED_MODE: int = _MODES.index('bounce')

_KEYS_TO_FLAGS = {
    'b': '--bitrate',
    't': '--thread',
    'o': '--output',
    'c': '--compression',
    's': '--smoothing',
}


def stage1():
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
        key_pressed = get_key_press()
        if set_selected_mode(key_pressed):
            if _MODES[_SELECTED_MODE] == ['keyframes', 'angle', 'transparency']:
                _KEYS_TO_FLAGS['x'] = f'--{_MODES[_SELECTED_MODE]}'
            elif _MODES[_SELECTED_MODE] in ['bounce', 'shutter']:
                _KEYS_TO_FLAGS['x'] = '--tempo'
            break


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--lang', choices=localization.get_locales(), default='en_us')
    args = parser.parse_args()

    localization.set_locale(args.lang)

    stage1()
