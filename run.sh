#!/bin/sh
# Print Ascii Art
echo "           
 __          __        _          _____    __          __  _     __  __ 
 \ \        / /       | |        |  __ \   \ \        / / | |   |  \/  |
  \ \  /\  / /_ _  ___| | ___   _| |__) |   \ \  /\  / /__| |__ | \  / |
   \ \/  \/ / _\` |/ __| |/ / | | |  ___/ | | \ \/  \/ / _ \ '_ \| |\/| |
    \  /\  / (_| | (__|   <| |_| | |   | |_| |\  /\  /  __/ |_) | |  | |
     \/  \/ \__,_|\___|_|\_\\\\__, |_|    \__, | \/  \/ \___|_.__/|_|  |_|
                             __/ |       __/ |                          
                            |___/       |___/                           
"

echo "Testing for FFmpeg, FFprobe and Python..."
if ! command -v ffmpeg &>/dev/null; then echo "FFmpeg not found, exiting..." && exit 1; fi
if ! command -v ffprobe &>/dev/null; then echo "FFprobe not found, exiting..." && exit 1; fi
if ! command -v python &>/dev/null; then echo "Python not found, exiting..." && exit 1; fi
echo "No issues found!"

# TODO: Write dependency check for python packages

read -p "Enter the language [en_us]: " lang
lang=${lang:-en_us}

echo "Starting UI"
python terminal_ui.py --lang $lang
