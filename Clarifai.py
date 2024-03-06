import os
import platform
from clarifai_grpc.channel.clarifai_channel import ClarifaiChannel
from clarifai_grpc.grpc.api import resources_pb2, service_pb2, service_pb2_grpc
from clarifai_grpc.grpc.api.status import status_code_pb2

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

    # Your PAT (Personal Access Token) can be found in the portal under Authentication
    PAT = '61a378e23e3041e1b8494551fe5564ab'
    USER_ID = 'wizardlm'
    APP_ID = 'generate'
    MODEL_ID = 'wizardCoder-Python-34B'
    MODEL_VERSION_ID = 'c15627f6d6de4090b5834866c1f17abe'
    RAW_TEXT = f"""You are designated as a QGPT Agent, a specialized QGIS Assistant Plugin, operating within QGIS version {version} on the {os_name} {os_version} operating system. Your core functionality involves interpreting instructions encapsulated within angle brackets <> and translating them into executable Python code compatible with the QGIS Python plugin environment. This includes managing all necessary imports to ensure the code runs seamlessly within QGIS.

    When the provided instruction necessitates downloading data, adhere to the following protocol:
    - Employ the urllib.request library for data retrieval, constructing requests as follows: req = urllib.request.Request(url, headers=headers); response = urllib.request.urlopen(req). Utilize the user agent string 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'.
    - Source data files from reputable and current databases such as Natural Earth, GADM, Humanitarian Data Exchange, or OpenStreetMap (OSM).

    Ensure that all processed outputs are directed to a temporary directory, as determined by tempfile.gettempdir(), and are subsequently opened for review.

    Your output will be Python code enclosed within triple brackets [[[ CODE ]]], formatted for direct execution via the exec() function. The code should not exceed 500 words and must adhere to the following criteria:
    - Simplicity is paramount.
    - The code should be well-organized and formatted for readability.
    - Exclude any comment lines beginning with #.
    - Incorporate print statements to display results following each operational step.

    Interpret the following command: <{user_input}>"""

    channel = ClarifaiChannel.get_grpc_channel()
    stub = service_pb2_grpc.V2Stub(channel)

    metadata = (('authorization', 'Key ' + PAT),)

    userDataObject = resources_pb2.UserAppIDSet(user_id=USER_ID, app_id=APP_ID)

    post_model_outputs_response = stub.PostModelOutputs(service_pb2.PostModelOutputsRequest(user_app_id=userDataObject,
        model_id=MODEL_ID, version_id=MODEL_VERSION_ID,
        inputs=[resources_pb2.Input(data=resources_pb2.Data(text=resources_pb2.Text(raw=RAW_TEXT)))]), metadata=metadata)
    if post_model_outputs_response.status.code != status_code_pb2.SUCCESS:
        print(post_model_outputs_response.status)
        raise Exception(f"Post model outputs failed, status: {post_model_outputs_response.status.description}")

    # Since we have one input, one output will exist here
    output = post_model_outputs_response.outputs[0]

    return output.data.text.raw

print(process_user_input('Download and show a world map polygon'))