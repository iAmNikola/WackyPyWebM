import json
import re
import subprocess
from pathlib import Path
from typing import List, Tuple

from data import FrameAudioLevel
from localization import localize_str
from tmp_paths import TmpPaths
from util import get_valid_path

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


def get_video_info(video_path: Path) -> Tuple[Tuple[int, int], str, int, int]:
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
    except subprocess.CalledProcessError as e:
        ffmpeg_error_handler(e.stderr)
    stream_data = json.loads(video_data.stdout)['streams'][0]
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
        print(localize_str('no_audio'))
        return False
    return True


def split_frames(video_path: Path, transparent: bool, threads: int):
    command = ['ffmpeg', '-threads', f'{threads}', '-y']
    if transparent:
        command += ['-vcodec', 'libvpx']
    command += ['-i', video_path, TmpPaths.tmp_frame_files]
    try:
        out = subprocess.run(command, bufsize=_MAX_BUFFER_SIZE, capture_output=True, check=True)
    except subprocess.CalledProcessError as e:
        ffmpeg_error_handler(e.stderr)


def exec_command(command: List[str], extra_data: Tuple[List[bool], int, int, int] = None):
    try:
        out = subprocess.run(command, bufsize=_MAX_BUFFER_SIZE, capture_output=True, check=True)
    except subprocess.CalledProcessError as e:
        ffmpeg_error_handler(e.stderr)
    if extra_data:
        frames_processed, index, same_size_count, num_frames = extra_data
        for i in range(index - same_size_count - 1, index - 1):
            frames_processed[i] = True
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
            end='\r',
        )


def get_frames_audio_levels(video_path: Path):
    try:
        frames_dbs = subprocess.run(
            # fmt:off
            [
                'ffprobe', '-f', 'lavfi',
                '-i', f"amovie={get_valid_path(video_path, filter=True)},astats=metadata=1:reset=1",
                '-show_entries', 'frame=pkt_pts_time:frame_tags=lavfi.astats.Overall.RMS_level',
                '-of', 'json',
            ],
            # fmt:on
            bufsize=_MAX_BUFFER_SIZE,
            capture_output=True,
            check=True,
        )
    except subprocess.CalledProcessError as e:
        ffmpeg_error_handler(e.stderr)

    highest: float = None
    frames_audio_levels: List[FrameAudioLevel] = []
    dbs_sum = 0
    for frame_dbs in json.loads(frames_dbs.stdout)['frames']:
        fal = FrameAudioLevel.from_dict(frame_dbs)
        frames_audio_levels.append(fal)

        if highest is None:
            highest = fal.dbs
        else:
            if fal.dbs > highest:
                highest = fal.dbs

        dbs_sum += fal.dbs if fal.dbs != float('-inf') else 0

    if highest == float('-inf'):
        print(localize_str('no_audio'))

    average = dbs_sum / len(frames_audio_levels)
    deviation = abs((highest - average) / 2)

    for fal in frames_audio_levels:
        clamped = max(min(fal.dbs, (average + deviation)), (average - deviation))
        v = abs((clamped - average) / deviation) * 0.5
        fal.percent_max = (0.5 + v) if clamped > average else (0.5 - v)

    return frames_audio_levels
