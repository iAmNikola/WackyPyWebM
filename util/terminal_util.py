import os

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

    Enter will return "\\r" on all platforms (without the space seen here)
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


def terminal_clear():
    os.system('cls' if os.name == 'nt' else 'clear')


def fix_terminal():
    os.system('echo on' if os.name == 'nt' else 'stty echo')


class KeyCodes:
    quit = ('\x1a', '\x03')
    arrow_up = ('\x1b[A', '\x00H')
    arrow_down = ('\x1b[B', '\x00P')
    arrow_right = ('\x1b[C', '\x00M')
    arrow_left = ('\x1b[D', '\x00K')
    enter = '\r'


def get_key_press():
    key = getch_but_it_actually_works()
    if key in KeyCodes.quit:
        raise KeyboardInterrupt
    if key.upper() == 'Q':
        sys.exit()
    return key
