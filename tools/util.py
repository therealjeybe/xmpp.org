import os
from pathlib import Path
import shutil

import requests

DOWNLOAD_PATH = Path('downloads')


def initialize_directory(path: Path) -> None:
    '''
    Remove path (if it exists) and containing files, then recreate path
    '''
    if path.exists() and path.is_dir():
        shutil.rmtree(path)
        os.mkdir(path)
    else:
        os.mkdir(path)


def download_file(url: str, path: Path) -> bool:
    '''
    Downloads file from url and stores it in /downloads/path
    returns success
    '''
    try:
        file_request = requests.get(url, stream=True, timeout=5)
    except requests.exceptions.RequestException as err:
        print('Error while requesting file', err)
        return False

    if not 200 >= file_request.status_code < 400:
        print('Error while trying to download from', url)
        return False

    with open(DOWNLOAD_PATH / path, 'wb') as data_file:
        max_size = 1024 * 1024 * 10  # 10 MiB
        size = 0
        for chunk in file_request.iter_content(chunk_size=8192):
            data_file.write(chunk)
            size += len(chunk)
            if size > max_size:
                file_request.close()
                print('File size exceeds 10 MiB:', path)
                return False
    return True
