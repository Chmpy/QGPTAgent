import os
import platform
import configparser
from pathlib import Path

import aiohttp
import requests

from .classes import Result


def process_user_input(user_input):
    """
    This function takes a user input, processes it through the Clarifai API with the current MODEL_ID, and returns the output.

    Parameters:
    user_input (str): The user's input to be processed.

    Returns:
    str: The raw text output from the Clarifai API.
    """
    # If no version is found, use QGIS 3.34.3 'Prizren' as default
    try:
        import qgis.utils
        version = qgis.utils.QGis.QGIS_VERSION
    except:
        version = '3.34.3'

    os_name = os.name
    os_version = platform.version()

    role = f"""You are designated as a QGPT Agent, a specialized QGIS Assistant Plugin, operating within QGIS version {version} on the {os_name} {os_version} operating system. Your core functionality involves interpreting instructions encapsulated within angle brackets <> and translating them into executable Python code compatible with the QGIS Python plugin environment. This includes managing all necessary imports to ensure the code runs seamlessly within QGIS.

    When the provided instruction necessitates downloading data, adhere to the following protocol:
    - Employ the urllib.request library for data retrieval, constructing requests as follows: req = urllib.request.Request(url, headers=headers); response = urllib.request.urlopen(req). Utilize the user agent string 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'.
    - Source data files from reputable and current databases such as Natural Earth, GADM, Humanitarian Data Exchange, or OpenStreetMap (OSM).

    Ensure that all processed outputs are directed to a temporary directory, as determined by tempfile.gettempdir(), and are subsequently opened for review.

    Your output will be Python code enclosed within triple brackets [[[ CODE ]]], formatted for direct execution via the exec() function. The code should not exceed 500 words and must adhere to the following criteria:
    - Simplicity is paramount.
    - The code should be well-organized and formatted for readability.
    - Exclude any comment lines beginning with #.
    - Incorporate print statements to display results following each operational step."""

    path = Path(__file__).parent.absolute()
    config_path = os.path.join(path, "config.ini")
    config = configparser.ConfigParser()
    config.read(config_path)

    url = config.get('api', 'endpoint_url') + "/v1/chat/completions"
    key = config.get('api', 'endpoint_key')
    temperature = config.get('api', 'endpoint_temp')
    max_tokens = config.get('api', 'endpoint_max_tokens')

    # Define the request headers
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer {}".format(key),
    }

    # Define the request payload
    payload = {
        "messages":
            [
                {
                    "role": "system",
                    "content": role
                },
                {
                    "role": "user",
                    "content": user_input
                }
            ],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code == 200:
        result_dict = response.json()
        result = Result(**result_dict)
        return result.choices.message.content
    else:
        print("Error:", response.status_code, response.text)
