import tempfile
from pathlib import Path


class TmpPaths:
    temp_dir: tempfile.TemporaryDirectory
    tmp_folder: Path
    tmp_frames: Path
    tmp_resized_frames: Path
    tmp_audio: Path
    tmp_concat_list: Path
    tmp_frame_files: Path

    @classmethod
    def build_tmp_paths(cls):
        cls.temp_dir = tempfile.TemporaryDirectory()
        cls.tmp_folder = Path(cls.temp_dir.name)

        cls.tmp_frames = cls.tmp_folder / 'tempFrames'
        cls.tmp_frames.mkdir(parents=True, exist_ok=True)
        cls.tmp_resized_frames = cls.tmp_folder / 'tempResizedFrames'
        cls.tmp_resized_frames.mkdir(parents=True, exist_ok=True)

        cls.tmp_audio = cls.tmp_folder / 'tempAudio.webm'
        cls.tmp_concat_list = cls.tmp_folder / 'tempConcatList.txt'
        cls.tmp_frame_files = cls.tmp_frames / '%05d.png'

    @classmethod
    def cleanup(cls):
        cls.temp_dir.cleanup()
