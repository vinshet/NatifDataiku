import requests
import json
from dataiku.customrecipe import *
# Retreives the bearer token from the login credentials
def retreive_bearer_token(endpoint,usr,pwd):
    headers = {
        "accept": "application/json",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    data = {"grant_type": "", "username": usr, "password": pwd}

    response = requests.post(endpoint + "/token", headers=headers, data=data)
    if response.status_code >= 400:
        return ""
    res_json = response.json()
    bearer_token = res_json["access_token"]
    # Bearer token for API usage
    bearer = "Bearer " + bearer_token
    return bearer

# Creates a folder (Uploaded folder) cointaining all the unprocessed input files for Deep-OCR/Extractions
def create_uploaded_folder(input_handle,output_handle):
    input_folder_paths = input_handle.list_paths_in_partition()
    output_folder_paths = output_handle.list_paths_in_partition()
    for path in input_folder_paths:
        data = ""
        with input_handle.get_download_stream(path) as fil:
            data = fil.read()
        upload_output_folder = "/Uploaded_files" + path
        if os.path.basename(path) in ("error_log.txt", "info_log.txt"):
            with output_handle.get_writer("/Processed_files" + path) as w:
                w.write(data)
        else:
            if upload_output_folder not in output_folder_paths:
                with output_handle.get_writer("/Uploaded_files" + path) as w:
                    w.write(data)

