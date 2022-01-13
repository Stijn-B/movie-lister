import shutil
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import imdb
from selenium.webdriver.common.by import By

from chromedriver import init_browser
from subtitles import get_embedded_subtitles, merge_all, VALID_FFMPEG_SUFFIXES
from util import parse_movie_name_from_string, recursive_iterdir, sanitize_name

IMDB_API = imdb.IMDb()

MOVIE_SUFFIXES = ['.mp4', '.mkv', '.avi']


@dataclass
class Movie:
    name: str
    year: int

    def __str__(self):
        return f'{self.name} ({self.year})'


# # # # # IMDB API

def query_movie_data_imdb(movie_filename: str) -> Movie:
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


def query_movie_data_google(movie_filename: str) -> Movie:
    """
    Uses google search to determine the official movie name and release year.
    """
    global SELENIUM_BROWSER
    if 'SELENIUM_BROWSER' not in globals():
        SELENIUM_BROWSER = init_browser(headless=False)

    # Search for imdb page of the movie
    search_term = 'imdb ' + movie_filename.replace('.', ' ')
    search_url = f'https://www.google.com/search?q={search_term.replace(" ", "+")}&hl=en'
    SELENIUM_BROWSER.get(search_url)

    # "iUh30" is class name of the first google search result irrespective of the keyword searched.
    result = SELENIUM_BROWSER.find_element(By.CLASS_NAME, 'iUh30')
    result.click()
    time.sleep(1)

    # Get title and year from imdb page
    result = SELENIUM_BROWSER.find_element(By.CLASS_NAME, 'TitleHeader__TitleText-sc-1wu6n3d-0')
    name = result.text
    result = SELENIUM_BROWSER.find_element(By.CLASS_NAME, 'TitleBlockMetaData__ListItemText-sc-12ein40-2')
    year = result.text

    return Movie(name=name, year=int(year))


# # # # # PROCESSING

def process_folder_contents(src_folder: Path, dst_folder: Optional[Path], delete_source: bool = False):
    """
    Cleans up all movie files and folders in the given directory; sanitizing names and embedding subtitle files.
    optional dst_folder: moves the results to this folder
    """
    for path in src_folder.iterdir():
        if path.is_file():
            if path.suffix not in MOVIE_SUFFIXES:
                continue
            print(f'file {path.name}')
            result = process_movie_file(path, dst_folder, delete_source)
            print(f'=> {result.name}')
        elif path.is_dir():
            print(f'folder {path.name}')
            result = process_movie_folder(path, dst_folder, delete_source)
            print(f'=> {result.name}')
        else:
            raise FileNotFoundError


def process_movie_file(movie_file: Path, dst_folder: Optional[Path], delete_source: bool = False) -> Path:
    assert movie_file.suffix in MOVIE_SUFFIXES

    # Determine filename to '<movie> (<year>)'
    movie = query_movie_data_google(movie_file.stem)
    dst_file = (dst_folder or movie_file.parent) / (sanitize_name(str(movie)) + movie_file.suffix)

    # File operations
    if movie_file != dst_file:
        shutil.copy(movie_file, dst_file)
        if delete_source:
            movie_file.unlink()

    return dst_file


def process_movie_folder(movie_folder: Path, dst_folder: Optional[Path], delete_source: bool = False) -> Path:
    dst_folder = dst_folder or movie_folder

    # Determine the Movie and Subtitle files
    files = recursive_iterdir(movie_folder)
    movie_files = [file for file in files if file.suffix in MOVIE_SUFFIXES]
    subtitle_files = [file for file in files if file.suffix in ['.srt']]

    # Select the largest movie file (smaller files are probably samples)
    movie_file = max(movie_files, key=lambda file: file.stat().st_size)

    # if 'movie already has embedded subtitles'
    #   or 'there are no srt files'
    #   or 'file type can't be used to embed subtitles'
    # -> process movie file without embedding subtitles
    if get_embedded_subtitles(movie_file) \
            or not subtitle_files \
            or movie_file.suffix not in VALID_FFMPEG_SUFFIXES:
        dst_file = process_movie_file(movie_file, dst_folder, delete_source)
    else:
        movie = query_movie_data_google(movie_folder.stem)
        dst_file = (dst_folder or movie_file.parent) / (sanitize_name(str(movie)) + movie_file.suffix)
        merge_all(movie_file, subtitle_files, dst_file)

    if delete_source and movie_folder != dst_folder:
        shutil.rmtree(str(movie_folder))

    return dst_file
