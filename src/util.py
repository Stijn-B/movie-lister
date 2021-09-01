import math
from pathlib import Path
from typing import List, Generator


def string_contains_number(string: str) -> bool:
    for letter in string:
        if letter.isnumeric():
            return True
    return False


def represents_int(s: str) -> bool:
    try:
        int(s)
        return True
    except ValueError:
        return False


def sanitize_name(name: str) -> str:
    """ Removes all backslashes (\\) and colons (:) """
    return name.replace('\\', '').replace(':', ' -')


def get_shared_prefix(strings: List[str]) -> str:
    if len(strings) == 0:
        return ''
    elif len(strings) == 1:
        return strings[0]

    # get the shared prefix of the names
    first_string, shared_prefix = strings[0], ''
    i = 0
    while i < len(first_string):
        if math.prod([string.startswith(first_string[:i]) for string in strings]):
            shared_prefix = first_string[:i]
        else:
            break
        i += 1

    return shared_prefix


def parse_movie_name_from_string(raw_name: str) -> str:
    """ Intended to parse a movie name from a torrent filename """
    raw_name = raw_name.replace('.', ' ').replace('_', ' ').replace('(', '').replace(')', '')

    # Take words up to the first word that contains a number
    name = []
    for word in raw_name.split(' '):
        if string_contains_number(word):
            break
        name.append(word)
    movie_name = ' '.join(name)

    # Remove everything between [] brackets
    movie_name = ' '.join([word for word in movie_name.split(' ') if not (word.startswith('[') or word.endswith(']'))])

    return movie_name


def recursive_iterdir(path: Path) -> Generator[Path, None, None]:
    if path.is_file():
        yield path
    elif path.is_dir():
        for sub_path in path.iterdir():
            yield from recursive_iterdir(sub_path)
    else:
        raise FileNotFoundError({'message:' f'path.is_file() and path.is_dir() are both False'})
