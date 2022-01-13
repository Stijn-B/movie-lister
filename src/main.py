from pathlib import Path

from movies import process_folder_contents


def __main__():
    torrent_folder = Path('/home/stijn/Torrents')
    video_folder = Path('/home/stijn/Videos')

    process_folder_contents(torrent_folder, video_folder)


if __name__ == '__main__':
    __main__()
