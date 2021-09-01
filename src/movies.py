import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import imdb

from src.util import parse_movie_name_from_string, get_files
from subtitles import get_embedded_subtitles, merge_all, VALID_FFMPEG_SUFFIXES
from util import sanitize_name

IMDB_API = imdb.IMDb()

MOVIE_SUFFIXES = ['.mp4', '.mkv', '.avi']


@dataclass
class Movie:
    name: str
    year: int

    def __str__(self):
        return f'{self.name} ({self.year})'


# # # # # IMDB API

def query_movie_data(movie_filename: str) -> Movie:
    """
    Parses the filename and attempts to query the IMDB API for the official movie name and release year.
    """
    global IMDB_API
    if 'IMDB_API' not in globals():
        IMDB_API = imdb.IMDb()

    name = parse_movie_name_from_string(movie_filename)

    results = IMDB_API.search_movie(name, 1)  # Get the 1st query result
    result = results[0]

    return Movie(result['title'], result['year'])


# # # # # PROCESSING

def process_folder_contents(src_folder: Path, dst_folder: Optional[Path]):
    """
    Cleans up all movie files and folders in the given directory; sanitizing names and embedding subtitle files.
    optional dst_folder: moves the results to this folder
    """
    for path in src_folder.iterdir():
        if path.is_file():
            if path.suffix not in MOVIE_SUFFIXES:
                continue
            print(f'file {path.name}')
            result = sanitize_movie_filename(path, dst_folder)
            print(f'=> {result.name}')
        elif path.is_dir():
            print(f'folder {path.name}')
            result = process_movie_folder(path, dst_folder)
            print(f'=> {result.name}')
        else:
            raise FileNotFoundError


def sanitize_movie_filename(movie_file: Path, dst_folder: Optional[Path]) -> Path:
    assert movie_file.suffix in MOVIE_SUFFIXES

    dst_folder = dst_folder or movie_file.parent

    movie = query_movie_data(movie_file.stem)

    # Rename file to '<movie> (<year>)'
    dst_file = dst_folder / (sanitize_name(str(movie)) + movie_file.suffix)
    movie_file.rename(dst_file)

    return dst_file


def process_movie_folder(movie_folder: Path, dst_folder: Path) -> Path:
    movie = query_movie_data(movie_folder.stem)

    # Determine the Movie and Subtitle files
    files = get_files(movie_folder)
    movie_files = [file for file in files if file.suffix in MOVIE_SUFFIXES]
    subtitle_files = [file for file in files if file.suffix in ['.srt']]

    # Select the largest movie file (smaller files are probably samples)
    movie_file = max(movie_files, key=lambda file: file.stat().st_size)
    dst_file = dst_folder / (sanitize_name(str(movie)) + movie_file.suffix)

    # if 'movie already has embedded subtitles'
    #   or 'there are no srt files'
    #   or 'file type can't be used to embed subtitles'
    # then: just rename
    if not subtitle_files or get_embedded_subtitles(movie_file) or movie_file.suffix not in ['.mp4', '.mkv']:
        movie_file.rename(dst_file)
    else:
        merge_all(movie_file, subtitle_files, dst_file)

    shutil.rmtree(str(movie_folder))

    return dst_file
