from pathlib import Path
import shutil


class TmpPaths:
    tmp_folder: Path = None
    tmp_frames: Path = None
    tmp_resized_frames: Path = None
    tmp_audio: Path = None
    tmp_concat_list: Path = None
    tmp_frame_files: Path = None

    @classmethod
    def build_tmp_paths(cls):
        tmp_folder = Path(__file__).resolve().parent / 'tempFiles'

        tmp_frames = tmp_folder / 'tempFrames'
        tmp_frames.mkdir(parents=True, exist_ok=True)
        tmp_resized_frames = tmp_folder / 'tempResizedFrames'
        tmp_resized_frames.mkdir(parents=True, exist_ok=True)

        tmp_audio = tmp_folder / 'tempAudio.webm'
        tmp_concat_list = tmp_folder / 'tempConcatList.txt'
        tmp_frame_files = tmp_frames / '%05d.png'

        cls.tmp_folder = tmp_folder
        cls.tmp_frames = tmp_frames
        cls.tmp_resized_frames = tmp_resized_frames
        cls.tmp_audio = tmp_audio
        cls.tmp_concat_list = tmp_concat_list
        cls.tmp_frame_files = tmp_frame_files

    @classmethod
    def cleanup(cls):
        shutil.rmtree(TmpPaths.tmp_folder)

