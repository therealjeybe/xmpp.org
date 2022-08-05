from typing import Union

import json
import os
from pathlib import Path
import subprocess

import requests

DOWNLOAD_PATH = Path('downloads')
DATA_PATH = Path('data')
COMPLIANCE_SUITE_URL = 'https://xmpp.org/extensions/xep-0459.xml'
COMPLIANCER_BUILD_URL = 'https://prosody.im/files/compliance'


def download_file(url: str, path: Path) -> bool:
    '''
    Downloads file from url and stores it in /downloads/path
    returns success
    '''
    file_request = requests.get(url, stream=True, timeout=5)
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


def generate_compliance_json() -> None:
    '''
    Runs the 'compliancer' tool to generate a 'comppliance_suite.json' file
    '''
    try:
        result = subprocess.check_output([
            'lua',
            f'{DOWNLOAD_PATH}/compliancer',
            '-v',
            f'{DOWNLOAD_PATH}/compliance-suite.xml'])
        json_result = json.loads(result)
        with open(DATA_PATH / 'compliance_suite.json',
                  'w',
                  encoding='utf-8') as compliance_suite_file:
            json.dump(json_result, compliance_suite_file, indent=4)
    except subprocess.CalledProcessError as err:
        print(err)


def check_packages_compliance() -> None:
    '''
    Runs the 'compliancer' tool against every package's DOAP file and adds the
    result to '{clients,libraries,servers}_list.doap'
    '''
    def add_compliance_data(package_type: str) -> None:
        with open(DATA_PATH / f'{package_type}_list_doap.json',
                  'rb') as json_file:
            clients_list = json.load(json_file)

        for _platform, clients in clients_list.items():
            for client in clients:
                compliance_data = compliance_dict.get(client['name'])
                if compliance_data is None:
                    client['badges'] = {}
                    continue
                client['badges'] = compliance_data['badges']

        with open(DATA_PATH / f'{package_type}_list_doap.json',
                  'w',
                  encoding='utf-8') as clients_data_file:
            json.dump(clients_list, clients_data_file, indent=4)

    compliance_dict: dict[str,
                          dict[str, Union[str, dict[str, list[str]]]]] = {}
    for subdir, _dirs, files in os.walk(f'{DOWNLOAD_PATH}/doap_files'):
        for file in files:
            try:
                result = subprocess.check_output([
                    'lua',
                    f'{DOWNLOAD_PATH}/compliancer',
                    '-v',
                    f'{DOWNLOAD_PATH}/compliance-suite.xml',
                    os.path.join(subdir, file)])
                json_result = json.loads(result)
                compliance_dict[json_result['name']] = json_result
            except subprocess.CalledProcessError as err:
                print(err)
    add_compliance_data('clients')
    add_compliance_data('libraries')
    add_compliance_data('servers')


if __name__ == '__main__':
    download_file(
        COMPLIANCE_SUITE_URL, 'compliance-suite.xml')
    download_file(COMPLIANCER_BUILD_URL, 'compliancer')
    generate_compliance_json()
    check_packages_compliance()
