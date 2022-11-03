import argparse
import os

import localization

if os.name == 'nt':
    os.system('color')
    

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--lang', choices=localization.get_locales(), default='en_us')
    args = parser.parse_args()

    localization.set_locale(args.lang)

