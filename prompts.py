import platform
import qgis.utils

version = qgis.utils.Qgis.QGIS_VERSION


# get completion
def make_prompt(prompt_type):
    prompt_type = int(prompt_type)
    # Get the name of the operating system
    os_name = platform.system()
    # Get the version of the operating system
    os_version = platform.release()
    # Prompt Engineering part
    # print(prompt_type)
    # ------------------------------------------------------------------------------------------------------------------
    prompt = f"""
    You are a QGPT Agent, a QGIS Assistant Plugin, running on QGIS version {version} and {os_name} {os_version} operating system.
     Your task is to take user input and generate Python code that can be fully executed within a QGIS Python plugin. Include all necessary imports.

    When the task involves downloading data, use the python urllib.request library.
    Set the user agent to 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'.
    Download files from reputable sources such as Natural Earth, GADM, Humanitarian Data Exchange, or OSM.

    Save all processing outputs into the temporary directory indicated by tempfile.gettempdir(), and ensure they can be opened for viewing.

    Your output should consist solely of Python code, enclosed within triple brackets like this: [[[ CODE ]]].
    The code should be formatted to be executed directly using the exec() function, be concise, and clear, without any comments (lines starting with #).
    After each step, print the results.

    Restrictions:
    - The complete output should be less than 500 words.
    - Include all necessary library imports.
    - Keep the code as simple and well-formatted as possible.

    Please provide the Python code following these guidelines.
    """
    if prompt_type in [0, 1]:
        # print(prompt)
        return prompt
    # ------------------------------------------------------------------------------------------------------------------
    # if layer is active
    if qgis.utils.iface.activeLayer():
        active_layer_info = f"""
        -QGIS Active Layer Name: {qgis.utils.iface.activeLayer().name()}
        -QGIS Active Layer CRS: {qgis.utils.iface.activeLayer().crs().authid()}
        -QGIS Active Layer Geometry Type: {qgis.utils.iface.activeLayer().geometryType()}
        -QGIS Active Layer Feature Count: {qgis.utils.iface.activeLayer().featureCount()}
        -QGIS Active Layer Extent: {qgis.utils.iface.activeLayer().extent()}
        -QGIS Active Layer Fields: {qgis.utils.iface.activeLayer().fields()}"""
    else:
        active_layer_info = f""""""

    prompt += f"""
    Here some infromation about QGIS WrokSpace:\
    -QGIS Current Project CRS: {qgis.utils.iface.mapCanvas().mapSettings().destinationCrs().authid()}. \
    -QGIS Current Project Extent: {qgis.utils.iface.mapCanvas().extent()}. \
    -QGIS Current Project Layers: {qgis.utils.iface.mapCanvas().layers()}. \
    -QGIS Current Project Layer Count: {qgis.utils.iface.mapCanvas().layerCount()} . \
    -QGIS Current Canvas Extent: {qgis.utils.iface.mapCanvas().extent()} . \
    {active_layer_info} . \
    
    """
    if prompt_type == 2:
        # print(prompt)
        return prompt


def make_debug_prompt(code, error):
    code = """from qgis.core import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import processing
from qgis.utils import *
import tempfile
""" + code + """# refresh the canvas
iface.mapCanvas().refresh()"""

    os_name = platform.system()
    # Get the version of the operating system
    os_version = platform.release()
    # Prompt Engineering part
    prompt = f"""You are QGPT Agent (QGIS Assistant Plugin ) running on QGIS version ({version}) and ({os_name} {os_version}) operation system \
    you provided the following python code:
{code}
The above code returns the error "{error}". Please briefly explain why the error is happening in one sentence bounded by brackets [[[ SENTENCE]]], then write the corrected python code bounded by brackets [[[ CODE ]]].
example: [[[Sentence ]]], [[[CODE]]]
"""
    return prompt


def make_chat_prompt():
    # Get the name of the operating system
    os_name = platform.system()
    # Get the version of the operating system
    os_version = platform.release()
    # Prompt Engineering part
    prompt = f"""Welcome to the QGPT Agent, your personal Geographical Information System expert! As a QGIS Assistant Plugin running on QGIS version {version} and {os_name} {os_version} operating system, I'm here to answer any questions you have related to GIS.

            Simply type your question and I'll provide you with a rich and informative answer in less than 200 words. My responses are precise and scientifically accurate, so you can trust that the information I provide is reliable.

            Whether you're looking to create maps, perform spatial analyses, or explore geographic data, I'm here to help. So go ahead and ask me anything related to GIS.

            """
    # print(prompt)
    return prompt
