import re
import json
import subprocess
from pathlib import Path
from typing import Tuple

from util import TMP_PATHS
from localization import localize_str

_MAX_BUFFER_SIZE = 1024 * 1000 * 8  # 8Mb


def ffmpeg_error_handler(stderr: str):
    error_message = re.findall(
        r'ffmpeg version [^\n]+\n(?:\s*built with [^\n]+\n|\s*lib[^\n]+\n|\s*configuration:[^\n]+\n)*([\s\S]*)',
        stderr,
    )[1]
    print(error_message)


def get_video_info(video_path: Path) -> Tuple[Tuple[int, int], str, int, int]:
    video_data = subprocess.run(
        [
            'ffprobe',
            '-v',
            'error',
            '-select_streams',
            'v',
            '-of',
            'json',
            '-count_frames',
            '-show_entries',
            'stream=r_frame_rate,width,height,nb_read_frames,bit_rate',
            f'{video_path}',
        ],
        bufsize=_MAX_BUFFER_SIZE,
        capture_output=True,
        text=True,
    )
    stream_data = json.loads(video_data.stdout)['streams']
    return (
        (stream_data['width'], stream_data['height']),
        stream_data['r_frame_rate'],
        int(stream_data['bit_rate']),
        int(stream_data['nb_read_frames']),
    )


def parse_fps(fps: str) -> float:
    if '/' in fps:
        fps = fps.split('/')
        return int(fps[0]) / int(fps[1])
    else:
        return float(fps)


def split_audio(video_path: Path) -> bool:
    tmp_audio = TMP_PATHS['tmp_audio']
    try:
        subprocess.run(
            [
                'ffmpeg',
                '-y',
                '-i',
                f'"{video_path}"',
                '-vn',
                '-c:a',
                'libvorbis',
                f'"{tmp_audio}"',
            ],
            bufsize=_MAX_BUFFER_SIZE,
            check=True,
        )
    except subprocess.CalledProcessError:
        print(localize_str('no_audio'))
        return False
    return True


def split_frames(video_path: Path, transparent: bool, threads: int):
    command = ['ffmpeg', '-threads', f'{threads}', '-y']
    if transparent:
        command += ['-vcodec', 'libvpx']
    tmp_frame_files = TMP_PATHS['tmp_frame_files']
    command += [f'"{video_path}"', f'"{tmp_frame_files}"']
    out = subprocess.run(command, bufsize=_MAX_BUFFER_SIZE, stderr=subprocess.PIPE, text=True)
    if out.stderr:
        ffmpeg_error_handler(out.stderr)
        exit()
