import json
import math
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

import localization
from modes.mode_base import FrameAudioLevel
from util.tmp_paths import TmpPaths

_MAX_BUFFER_SIZE = 1024 * 1000 * 8  # 8Mb


class FFMPEGExcption(Exception):
    ...


def ffmpeg_error_handler(stderr: bytes):
    error_message = re.findall(
        r'ffmpeg version [^\n]+\n(?:\s*built with [^\n]+\n|\s*lib[^\n]+\n|\s*configuration:[^\n]+\n)*([\s\S]*)',
        stderr.decode(),
    )
    if error_message:
        error_message = error_message[-1]
    else:
        error_message = stderr.decode()
    raise FFMPEGExcption(error_message)


def parse_fps(fps: str) -> float:
    if '/' in fps:
        parts = fps.split('/')
        return int(parts[0]) / int(parts[1])
    else:
        return float(fps)


def get_valid_path(path: Path, _filter=False) -> str:
    if os.name == 'nt':
        path = str(path).replace('\\', '/\\')
        if _filter:
            path = path.replace(':', r'\\:')
    return str(path)


def get_video_info(video_path: Path) -> Tuple[Tuple[int, int], str, Optional[int], int]:
    try:
        video_data = subprocess.run(
            # fmt:off
            [
                'ffprobe', '-v', 'error',
                '-select_streams', 'v', '-of', 'json',
                '-count_frames', '-show_entries',
                'stream=r_frame_rate,width,height,nb_read_frames,bit_rate',
                video_path,
            ],
            # fmt:on
            bufsize=_MAX_BUFFER_SIZE,
            capture_output=True,
            check=True,
        )
    except subprocess.CalledProcessError as error:
        ffmpeg_error_handler(error.stderr)

    stream_data: Dict[str, Any] = json.loads(video_data.stdout)['streams'][0]  # type: ignore
    return (
        (stream_data['width'], stream_data['height']),
        stream_data['r_frame_rate'],
        int(stream_data['bit_rate']) if stream_data.get('bit_rate') else None,
        int(stream_data['nb_read_frames']),
    )


def split_audio(video_path: Path) -> bool:
    try:
        out = subprocess.run(
            # fmt:off
            [
                'ffmpeg', '-y', '-i', video_path,
                '-vn', '-c:a', 'libvorbis', TmpPaths.tmp_audio,
            ],
            # fmt:on
            bufsize=_MAX_BUFFER_SIZE,
            capture_output=True,
            check=True,
        )
    except subprocess.CalledProcessError:
        localization.print('no_audio')
        return False

    return True


def split_frames(video_path: Path, transparent: bool, threads: int):
    command = ['ffmpeg', '-threads', f'{threads}', '-y']
    if transparent:
        command += ['-vcodec', 'libvpx']
    command += ['-i', video_path, '-q:v', '0', TmpPaths.tmp_frame_files]

    try:
        out = subprocess.run(command, bufsize=_MAX_BUFFER_SIZE, capture_output=True, check=True)
    except subprocess.CalledProcessError as error:
        ffmpeg_error_handler(error.stderr)


def exec_command(command: List[str], callback: Optional[Callable[[], None]] = None):
    try:
        out = subprocess.run(command, bufsize=_MAX_BUFFER_SIZE, capture_output=True, check=True)
    except subprocess.CalledProcessError as error:
        ffmpeg_error_handler(error.stderr)

    if callback:
        callback()


def get_frames_audio_levels(video_path: Path):
    try:
        out = subprocess.run(
            # fmt:off
            [
                'ffprobe', '-f', 'lavfi',
                '-i', f'amovie={get_valid_path(video_path, _filter=True)},astats=metadata=1:reset=1',
                '-show_entries', 'frame=pkt_pts_time:frame_tags=lavfi.astats.Overall.RMS_level',
                '-of', 'json',
            ],
            # fmt:on
            bufsize=_MAX_BUFFER_SIZE,
            capture_output=True,
            check=True,
        )
    except subprocess.CalledProcessError as error:
        ffmpeg_error_handler(error.stderr)

    highest: Optional[float] = None
    frames_audio_levels: List[FrameAudioLevel] = []
    dbs_sum = 0
    for frame_dbs in json.loads(out.stdout)['frames']:  # type: ignore
        fal = FrameAudioLevel(frame_dbs)
        frames_audio_levels.append(fal)

        if highest is None:
            highest = fal.dbs
        else:
            if fal.dbs > highest:
                highest = fal.dbs

        dbs_sum += fal.dbs if fal.dbs != float('-inf') else 0

    if highest is None or highest == float('-inf'):
        localization.print('no_audio')
        sys.exit(1)

    average = dbs_sum / len(frames_audio_levels)
    deviation = abs((highest - average) / 2)

    for fal in frames_audio_levels:
        clamped = max(min(fal.dbs, (average + deviation)), (average - deviation))
        v = abs((clamped - average) / deviation) * 0.5
        fal.percent_max = (0.5 + v) if clamped > average else (0.5 - v)

    return frames_audio_levels


def find_min_non_error_size(width: int, height: int) -> int:
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

    return 0
