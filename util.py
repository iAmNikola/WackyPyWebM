import math
import os
from pathlib import Path
from typing import Dict


def clear():
    os.system('cls' if os.name == 'nt' else 'clear')


def fix_terminal():
    print()
    os.system('' if os.name == 'nt' else 'stty echo')


####################################################################
##  Bless Markus Hirsimäki: https://stackoverflow.com/a/72035449  ##
####################################################################


def _read_one_wide_char_win():
    """Wait keyhit return chr. Get only 1st chr if multipart key like arrow"""
    return msvcrt.getwch()


def _char_can_be_escape_win(char):
    """Return true if char could start a multipart key code (e.g.: arrows)"""
    return True if char in ("\x00", "à") else False  # \x00 is null character


def _dump_keyboard_buff_win():
    """If piece of multipart keycode in buffer, return it. Else return None"""
    try:  # msvcrt.kbhit wont work with msvcrt.getwch
        msvcrt.ungetwch("a")  # check buffer status by ungetching wchr
    except OSError:  # ungetch fails > something in buffer so >
        return msvcrt.getwch()  # return the buffer note: win multipart keys
    else:  # are always 2 parts. if ungetwch does not fail
        _ = msvcrt.getwch()  # clean up and return empty string
        return ""


def _read_one_wide_char_nix():
    """Wait keyhit return chr. Get only 1st chr if multipart key like arrow"""
    old_settings = termios.tcgetattr(sys.stdin.fileno())  # save settings
    tty.setraw(sys.stdin.fileno())  # set raw mode to catch raw key w/o enter
    wchar = sys.stdin.read(1)
    termios.tcsetattr(sys.stdin.fileno(), termios.TCSANOW, old_settings)
    return wchar


def _char_can_be_escape_nix(char):
    """Return true if char could start a multipart key code (e.g.: arrows)"""
    return True if char == "\x1b" else False  # "\x1b" is literal esc-key


def _dump_keyboard_buff_nix():
    """If parts of multipart keycode in buffer, return them. Otherwise None"""
    old_settings = termios.tcgetattr(sys.stdin.fileno())  # save settings
    tty.setraw(sys.stdin.fileno())  # raw to read single key w/o enter
    os.set_blocking(sys.stdin.fileno(), False)  # dont block for empty buffer
    buffer_dump = ""
    while char := sys.stdin.read(1):
        buffer_dump += char
    os.set_blocking(sys.stdin.fileno(), True)  # restore normal settings
    termios.tcsetattr(sys.stdin.fileno(), termios.TCSANOW, old_settings)
    if buffer_dump:
        return buffer_dump
    else:
        return ""


if os.name == "nt":
    import msvcrt

    read_one_wdchar = _read_one_wide_char_win
    char_can_escape = _char_can_be_escape_win
    dump_key_buffer = _dump_keyboard_buff_win
if os.name == "posix":
    import sys
    import termios
    import tty

    read_one_wdchar = _read_one_wide_char_nix
    char_can_escape = _char_can_be_escape_nix
    dump_key_buffer = _dump_keyboard_buff_nix


def getch_but_it_actually_works() -> str:
    """Returns a printable character or a keycode corresponding to special key
    like arrow or insert. Compatible with windows and linux, no external libs
    except for builtins. Uses different builtins for windows and linux.

    This function is more accurately called:
    "get_wide_character_or_keycode_if_the_key_was_nonprintable()"

    e.g.:
        * returns "e" if e was pressed
        * returns "E" if shift or capslock was on
        * returns "x1b[19;6~'" for ctrl + shift + F8 on unix

    You can use string.isprintable() if you need to sometimes print the output
    and sometimes use it for menu control and such. Printing raw ansi escape
    codes can cause your terminal to do things like move cursor three rows up.

    Enter will return "\ r" on all platforms (without the space seen here)
    as the enter key will produce carriage return, but windows and linux
    interpret it differently in different contexts on higher level
    """
    wchar = read_one_wdchar()  # get first char from key press or key combo
    if char_can_escape(wchar):  # if char is escapecode, more may be waiting
        dump = dump_key_buffer()  # dump buffer to check if more were waiting.
        return wchar + dump  # return escape+buffer. buff could be just ""
    else:  # if buffer was empty then we return a single
        return wchar  # key like "e" or "\x1b" for the ESC button


#########################
## End of Markus' code ##
#########################

# Common keys codes
KEY_CODES = {
    'CTRL+[CZ]': ['\x1a', '\x03'],
    'ARROW_UP': ['\x1b[A', '\x00H'],
    'ARROW_DOWN': ['\x1b[B', '\x00P'],
    'ARROW_RIGHT': ['\x1b[C', '\x00M'],
    'ARROW_LEFT': ['\x1b[D', '\x00K'],
    'ENTER': '\r',
}


def get_key_press():
    key = getch_but_it_actually_works()
    if key in KEY_CODES['CTRL+[CZ]']:
        raise KeyboardInterrupt
    if key.upper() == 'Q':
        exit(0)
    return key


TMP_PATHS: Dict[str, Path] = {}


def build_tmp_paths():
    global TMP_PATHS
    tmp_folder = Path(__file__).resolve().parent / 'tempFiles'

    tmp_frames = tmp_folder / 'tempFrames'
    tmp_frames.mkdir(parents=True, exist_ok=True)
    tmp_resized_frames = tmp_folder / 'tempResizedFrames'
    tmp_resized_frames.mkdir(parents=True, exist_ok=True)

    tmp_audio = tmp_folder / 'tempAudio.webm'
    tmp_concat_list = tmp_folder / 'tempConcatList.txt'
    tmp_frame_files = tmp_frames / '%05d.png'

    TMP_PATHS['tmp_folder'] = tmp_folder
    TMP_PATHS['tmp_frames'] = tmp_frames
    TMP_PATHS['tmp_resized_frames'] = tmp_resized_frames
    TMP_PATHS['tmp_audio'] = tmp_audio
    TMP_PATHS['tmp_concat_list'] = tmp_concat_list
    TMP_PATHS['tmp_frame_files'] = tmp_frame_files


def find_min_non_error_size(width, height):
    def av_reduce_succeeds(num, den):
        MAX = 255
        a0 = [0, 1]
        a1 = [1, 0]
        gcd = math.gcd(num, den)

        if gcd > 1:
            num //= gcd
            den //= gcd

        if num <= MAX and den <= MAX:
            a1 = [num, den]
            den = 0

        while den:
            x = num // den
            next_den = num - den * x
            a2n = x * a1[0] + a0[0]
            a2d = x * a1[1] + a0[1]

            if a2n > MAX or a2d > MAX:
                if a1[0]:
                    x = (MAX - a0[0]) // a1[0]
                if a1[1]:
                    x = min(x, (MAX - a0[1]) // a1[1])
                if (den * (2 * x * a1[1] + a0[1])) > (num * a1[1]):
                    a1 = [x * a1[0] + a0[0], x * a1[1] + a0[1]]
                break

            a0 = a1
            a1 = [a2n, a2d]
            num = den
            den = next_den

        return math.gcd(a1[0], a1[1]) <= 1 and (a1[0] <= MAX and a1[1] <= MAX) and a1[0] > 0 and a1[1] > 0

    for i in range(1, max(width, height)):
        if av_reduce_succeeds(i, height) and av_reduce_succeeds(width, i):
            return i


def load_modes():
    modes = {}
    for mode in (Path(__file__).resolve().parent / 'modes').glob('*.py'):
        if mode.stem != 'mode_base':
            modes[mode.stem] = __import__(f'modes.{mode.stem}', fromlist=['Mode']).Mode
    return modes


def parse_fps(fps: str) -> float:
    if '/' in fps:
        fps = fps.split('/')
        return int(fps[0]) / int(fps[1])
    else:
        return float(fps)


def get_valid_path(path: Path, filter=False) -> str:
    if os.name == 'nt':
        path = str(path).replace('\\', '/\\')
        if filter:
            path = path.replace(':', r'\\:')
    return path
