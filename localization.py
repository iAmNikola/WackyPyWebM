import json
from pathlib import Path
from typing import Dict, List, Union


class Localization:
    current_locale: Dict[str, str] = {}
    folder = Path(__file__).resolve().parent / 'localization'


def get_locales() -> List[str]:
    locales = [localization_file.stem for localization_file in Localization.folder.glob('*.json')]
    return locales


def set_locale(lang) -> None:
    with open(Localization.folder / f'{lang}.json') as f:
        Localization.current_locale = json.load(f)


def localize_str(key: str, args: Union[Dict[str, str], None]) -> str:
    if key in Localization.current_locale:
        raw_text = Localization.current_locale[key]
    else:
        return Localization.current_locale['no_translation']

    if args:
        for arg, value in args.items():
            raw_text = raw_text.replace('{' + arg + '}', str(value))

    return raw_text


_print = print


def print(key: str, args: Dict[str, str] = None, end='\n', *other):
    _print(localize_str(key, args), *other, end=end)


def colored_print(key, args: Dict[str, str] = None, attrs: List[str] = None, *other):
    from termcolor import colored

    _print(colored(localize_str(key, args), attrs=attrs), *other)
