import json
import re
import subprocess
from pathlib import Path
from threading import Lock
from typing import List, Tuple

from localization import localize_str
from util import TMP_PATHS

_MAX_BUFFER_SIZE = 1024 * 1000 * 8  # 8Mb
_LOCK = Lock()


def ffmpeg_error_handler(stderr: str):
    error_message = re.findall(
        r'ffmpeg version [^\n]+\n(?:\s*built with [^\n]+\n|\s*lib[^\n]+\n|\s*configuration:[^\n]+\n)*([\s\S]*)',
        stderr,
    )[-1]
    print('FFMPEG ERROR:', error_message)


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
        encoding='utf-8',
    )
    stream_data = json.loads(video_data.stdout)['streams'][0]
    return (
        (stream_data['width'], stream_data['height']),
        stream_data['r_frame_rate'],
        int(stream_data['bit_rate']),
        int(stream_data['nb_read_frames']),
    )


def split_audio(video_path: Path) -> bool:
    tmp_audio = TMP_PATHS['tmp_audio']
    try:
        subprocess.run(
            [
                'ffmpeg',
                '-y',
                '-i',
                f'{video_path}',
                '-vn',
                '-c:a',
                'libvorbis',
                f'{tmp_audio}',
            ],
            bufsize=_MAX_BUFFER_SIZE,
            check=True,
            stderr=subprocess.PIPE,
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
    command += ['-i', f'{video_path}', f'{tmp_frame_files}']
    try:
        subprocess.run(command, bufsize=_MAX_BUFFER_SIZE, stderr=subprocess.PIPE, text=True, check=True)
    except subprocess.CalledProcessError as e:
        ffmpeg_error_handler(e.stderr)
        exit()


def exec_command(command: List[str], extra_data: Tuple[List[bool], int, int, int] = None):
    try:
        out = subprocess.run(command, bufsize=_MAX_BUFFER_SIZE, stderr=subprocess.PIPE, text=True, check=True)
    except subprocess.CalledProcessError as e:
        ffmpeg_error_handler(e.stderr)
        return
    if extra_data:
        frames_processed, index, same_size_count, num_frames = extra_data
        for i in range(index - same_size_count - 1, index - 1):
            frames_processed[i] = True
        _LOCK.acquire()
        print('\r', end='')
        print(
            localize_str(
                'convert_progress',
                args={
                    'framecount': f'{same_size_count:>5}',
                    'startframe': index - same_size_count,
                    'endframe': index,
                    'batch_size': num_frames,
                    'percent': f'{100*frames_processed.count(True) / num_frames:.1f}',
                },
            ),
            end='',
        )
        _LOCK.release()
