import argparse
import os
from pathlib import Path
from typing import Any, Dict, List, Tuple

from termcolor import colored

import localization
import wackypywebm
from util.args_util import IArgs, get_arg_desc
from util.terminal_util import KeyCodes, get_key_press, terminal_clear

if os.name == 'nt':
    os.system('color')


class TerminalUI:
    modes: List[str] = list(wackypywebm.MODES.keys())
    selected_mode: int = list(wackypywebm.MODES.keys()).index('bounce')


def mode_selection() -> Dict[str, str]:
    def draw():
        terminal_clear()
        localization.colored_print('select_mode_arrows', None, ['bold', 'underline'], '\n')
        tmp = []
        for mode in TerminalUI.modes:
            if TerminalUI.modes[TerminalUI.selected_mode] == mode:
                tmp.append(colored(mode, attrs=['underline']))
            else:
                tmp.append(mode)
        print('    '.join(tmp))

    def set_selected_mode(key) -> bool:
        if key == KeyCodes.enter:
            return True
        if key in KeyCodes.arrow_left:
            if TerminalUI.selected_mode == 0:
                TerminalUI.selected_mode = len(TerminalUI.modes) - 1
            else:
                TerminalUI.selected_mode -= 1
        if key in KeyCodes.arrow_right:
            if TerminalUI.selected_mode == (len(TerminalUI.modes) - 1):
                TerminalUI.selected_mode = 0
            else:
                TerminalUI.selected_mode += 1
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
            if TerminalUI.modes[TerminalUI.selected_mode] in ['keyframes', 'angle', 'transparency']:
                keys_to_flags['x'] = f'{TerminalUI.modes[TerminalUI.selected_mode]}'
            elif TerminalUI.modes[TerminalUI.selected_mode] in ['bounce', 'shutter']:
                keys_to_flags['x'] = 'tempo'
            return keys_to_flags


def set_options(keys_to_flags: Dict[str, str]) -> Tuple[Dict[str, str], Path]:
    flags: Dict[str, str] = {}

    def draw_options():
        terminal_clear()
        if TerminalUI.modes[TerminalUI.selected_mode] == 'keyframes':
            localization.colored_print('change_options_k', attrs=['bold', 'underline'])
        else:
            localization.colored_print('change_options', attrs=['bold', 'underline'])
        print()

        for key, flag in keys_to_flags.items():
            print(f'{key}: {get_arg_desc(flag)}')

        if flags:
            print()
            localization.colored_print('current_arg_values', attrs=['bold', 'underline'])
        for flag, value in flags.items():
            print(f'--{flag} = "{value}"')

    def draw_arg_input(flag: str):
        terminal_clear()
        localization.colored_print('enter_arg_value', args={'arg': flag}, attrs=['bold', 'underline'])
        if flags.get(flag):
            print(f'Current value: "{flags[flag]}"\n')

    def configure_options(key: str):
        if key == KeyCodes.enter:
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
        terminal_clear()
        if file_not_found:
            localization.colored_print('file_not_found', attrs=['bold', 'underline'])
        localization.colored_print('enter_file_path', attrs=['bold', 'underline'])

    draw_file_input()
    while True:
        file_path = Path(input()).resolve()
        if file_path.is_file():
            return flags, file_path
        draw_file_input(file_not_found=True)


def review_options(flags: Dict[str, Any], file_path: Path):
    def draw():
        terminal_clear()
        localization.colored_print('review_settings', attrs=['bold', 'underline'])
        localization.colored_print('r_s_mode', None, ['underline'], TerminalUI.modes[TerminalUI.selected_mode])
        localization.colored_print('r_s_args', attrs=['underline'])
        for key, value in flags.items():
            print(f'    {key}: "{value}"')
        localization.colored_print('r_s_file', None, ['underline'], file_path)

    draw()
    while True:
        if get_key_press() == KeyCodes.enter:
            if 'bitrate' not in flags:
                flags['bitrate'] = '1M'
            if 'threads' not in flags:
                cpu_count = os.cpu_count()
                flags['threads'] = cpu_count if cpu_count else 0 + 4
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
                flags['output'] = (
                    file_path.parent / f'{file_path.stem}_{TerminalUI.modes[TerminalUI.selected_mode]}.webm'
                )
            if 'keyframes' not in flags:
                flags['keyframes'] = None
            return IArgs(flags)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--language', choices=localization.get_locales(), default='en_us')
    args = parser.parse_args()

    localization.set_locale(args.language)

    KEYS_TO_FLAGS = mode_selection()
    FLAGS, FILE_PATH = set_options(KEYS_TO_FLAGS)
    FLAGS = review_options(FLAGS, FILE_PATH)

    wackypywebm.wackify([TerminalUI.modes[TerminalUI.selected_mode]], FILE_PATH, FLAGS, FLAGS.output)
