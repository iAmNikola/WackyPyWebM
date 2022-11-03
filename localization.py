import json
from pathlib import Path
from typing import List
from typing import Dict

_CURRENT_LOCALE: Dict[str, str] = {}
_LOCALIZATION_FOLDER = Path(__file__).resolve().parent / 'localization'


def get_locales() -> List[str]:
    locales = [localization_file.stem for localization_file in _LOCALIZATION_FOLDER.glob('*.json')]
    return locales


def set_locale(lang) -> None:
    global _CURRENT_LOCALE
    with open(_LOCALIZATION_FOLDER / f'{lang}.json') as f:
        _CURRENT_LOCALE = json.load(f)


def localize_str(key: str, args: Dict = None) -> str:
    if key in _CURRENT_LOCALE:
        raw_text = _CURRENT_LOCALE[key]
    else:
        return _CURRENT_LOCALE['no_translation']

    if args:
        for arg, value in args.items():
            raw_text.replace('{%s}'.format(arg), value)

    return raw_text
