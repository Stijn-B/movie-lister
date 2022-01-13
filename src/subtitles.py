import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from util import get_shared_prefix

VALID_FFMPEG_SUFFIXES = ['.mp4', '.mkv']


@dataclass
class Subtitle:
    name: str
    file: Path

    def __str__(self):
        return self.name


def sanitize_subtitle_names(subtitles: List[Subtitle]) -> List[Subtitle]:
    """
    Truncates the shared prefixes of the subtitle names.
    If only one subtitle is given, it's name is changed to 'subtitles'
    Example: ['abc_eng', 'abc_jap'] -> ['eng', 'jap']
    """

    if len(subtitles) == 1:
        subtitles[0].name = 'subtitles'
        return subtitles

    # get the shared prefix of the names
    shared_prefix = get_shared_prefix([sub_file.name for sub_file in subtitles])

    # remove the shared prefix
    for sub in subtitles:
        sub.name = sub.name[len(shared_prefix):]

    return subtitles


# # # # # FFMPEG

def get_embedded_subtitles(file: Path) -> List[str]:
    """
    Returns a list of embedded subtitle languages.
    Example: ['eng', 'swe', 'jap']
    """
    cmd = ['ffprobe', '-loglevel', 'error', '-select_streams', 's', '-show_entries',
           'stream=index:stream_tags=language', '-of', 'csv=p=0', str(file)]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p.communicate()
    if err:
        return []
    result = out.decode("utf-8")
    return [x.split(',')[1] for x in result.split('\n') if x != '']


def merge_all(video: Path, subtitle_files: List[Path], dest_file: Optional[Path]):
    """

    TODO: If no dest_file is given, the existing video file will be overwritten.
    The suffix of dest_file has to be the same as the source video!


    ffmpeg command sources:
        - https://stackoverflow.com/a/33289845/3179285
        - https://video.stackexchange.com/a/22198/34558

    Copy all audio and video streams, add multiple subtitle stream:
    > ffmpeg -i in.mp4 <n * -i subs.srt> \
        -map 0:v -map 0:a <n* -map <i>> \
        -c:v copy -c:a copy -c:s mov_text \
        <n * -metadata:s:s:0 language=<language>> \
        output.mp4
    example:
    > ffmpeg -i in.mp4 -i in_eng.srt -i in_dan.srt \
        -map 0:v -map 0:a -map 1 -map 2 \
        -c:v copy -c:a copy -c:s mov_text \
        -metadata:s:s:0 language=eng -metadata:s:s:1 language=dan \
        output.mp4
    """

    assert dest_file.suffix in VALID_FFMPEG_SUFFIXES

    subtitles = [Subtitle(sub.stem, sub) for sub in subtitle_files]
    subtitles = sanitize_subtitle_names(subtitles)

    print(f'Merging')
    print(f'  - {video.name}')
    sub_string = '\n  - '.join([f'{sub.file.name} as {sub.name}' for sub in subtitles])
    print(f'  - {sub_string}')

    # Generating ffmpeg command
    sub_files, sub_maps, sub_metadata, i = [], [], [], 0
    for sub in subtitles:
        sub_files.append('-i')
        sub_files.append(str(sub.file))
        sub_maps.append('-map')
        sub_maps.append(str(i + 1))
        sub_metadata.append(f'-metadata:s:s:{i}')
        sub_metadata.append(f'language={sub.name}')
        i += 1

    copy_subs_type = 'mov_text' if dest_file.suffix == '.mp4' else 'srt'  # .mp4: 'mov_text', .mkv: 'srt'

    cmd = [
        'ffmpeg', '-i', str(video), *sub_files,  # Input
        '-map', '0:v', '-map', '0:a', *sub_maps,  # Mapping Streams
        '-c:v', 'copy', '-c:a', 'copy', '-c:s', copy_subs_type,  # Copying
        *sub_metadata,  # Subtitle metadata (language)
        str(dest_file)  # Output
    ]

    # Executing ffmpeg command
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p.communicate()
    return out, err
