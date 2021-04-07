# Import the helpers for custom recipes
from dataiku.customrecipe import get_input_names_for_role, get_recipe_config, get_output_names_for_role
from modules import retreive_bearer_token, create_uploaded_folder

# -*- coding: utf-8 -*-
import dataiku
import requests
import json
import base64
import time
import os
import logging


def write_to_log(messages, proc_type, doc_type, log_type):
    global output_folder_paths
    document_type = ""
    existing_messages = ""
    if proc_type == "Deep-OCR" and doc_type == "other":
        document_type = ""
    else:
        document_type = str(doc_type + "/")
    if (
        str(
            "/Processed_files/"
            + proc_type
            + "/"
            + document_type
            + log_type
            + "_log.txt"
        )
        in output_folder_paths
    ):
        with output_handle.get_download_stream(
            "/Processed_files/"
            + proc_type
            + "/"
            + document_type
            + log_type
            + "_log.txt"
        ) as f:
            existing_messages = f.read()
            existing_messages=existing_messages.decode()
    if (
        existing_messages == "No errors recorded"
        or existing_messages == "No documents processed"
    ):
        existing_messages = ""
    with output_handle.get_writer(
        "/Processed_files/" + proc_type + "/" + document_type + log_type + "_log.txt"
    ) as w:
        w.write((str(existing_messages) + "\n" + messages).encode())
    output_folder_paths = output_handle.list_paths_in_partition()


# Uploads file to the api and returns the response
def upload_files(doc, doc_type):
    with input_handle.get_download_stream(doc) as f:
        upload = {
            "file": (doc, f)
        }  # To include just the filename use os.path.basename(doc)
        response = requests.post(
            endpoint + "/documents/?document_type=" + doc_type.lower() + "&language=xx",
            headers=headers,
            files=upload,
        )
        return response


# Retreives the processed file used for Deep-OCR and the Extractions. This file is resized for processing and is of the format .jpg
def retreive_processed_file(response):
    imgdata = list()
    for pages in response.json():
        document_data = pages["data"]
        # Locate the magic bytes for the jpg files(base64 encoded)
        offset = document_data.find("/9j/")
        imgdata.append(base64.b64decode(document_data[offset:]))
    return imgdata


def write_to_output_folder(
    proc_type, document_type_folder, document_name, file_name, data
):
    with output_handle.get_writer(
        "/Processed_files/"
        + proc_type
        + "/"
        + document_type_folder
        + document_name
        + "/"
        + file_name
    ) as w:
        w.write(data)


# Writes 3 files(or more based on the number of pages) namely upload_details.json,ocr_data.json/extractions_data.json.processed_file_page_(n)
# A folder is created with the name of the file and the above mentioned documents are placed there
# An example hierarchy for a document to be uploaded for Extractions post processing is /Processed_files/Extractions/Invoice/{Filename}/upload_details.json
def write_to_file_folder(
    file_name,
    proc_type,
    data_ocr,
    data_extractions,
    file_data,
    processed_file,
    file_type,
):
    document_type_folder = ""
    if proc_type == "Deep-OCR" and file_type == "other":
        document_type_folder = ""
    else:
        document_type_folder = str(file_type + "/")
        write_to_output_folder(
            proc_type,
            document_type_folder,
            file_name,
            "extractions_data.json",
            data_extractions,
        )
    write_to_output_folder(
        proc_type, document_type_folder, file_name, "upload_details.json", file_data
    )
    write_to_output_folder(
        proc_type, document_type_folder, file_name, "ocr_data.json", data_ocr
    )
    for i in range(0, len(processed_file)):
        write_to_output_folder(
            proc_type,
            document_type_folder,
            file_name,
            str("processed_file_page_" + str(i + 1) + ".jpg"),
            processed_file[i],
        )


def check_response(response_obj):
    if response_obj.status_code == 200 or response_obj.status_code == 201:
        return True
    elif response_obj.status_code == 402:
        return "quota_exceeded"
    else:
        return False


def get_details(info_type, uuid, proc_type, file_type, file_name):
    response = ""
    if info_type == "processed_doc":
        response = requests.get(
            endpoint + "/documents/" + uuid + "/processed", headers=headers
        )
    elif info_type == "extractions":
        response = requests.get(
            endpoint + "/documents/" + uuid + "/extractions", headers=headers
        )
    elif info_type == "ocr":
        response = requests.get(
            endpoint + "/documents/" + uuid + "/ocr?include_raw_types=false",
            headers=headers,
        )
    if check_response(response):
        write_to_log(
            "Success retreiving {} details for {}".format(
                str(info_type), str(file_name)
            ),
            proc_type,
            file_type,
            "info",
        )
        return response
    else:
        write_to_log(
            "Error retreiving {} details for {}".format(str(info_type), str(file_name)),
            proc_type,
            file_type,
            "error",
        )


# Retreives the information to be written into upload_details.json,ocr_data.json/extractions_data.json.processed_file_page_(n)
def get_processed_doc(file_info, proc_type, file_type):
    file_id = file_info["uuid"]
    file_name = os.path.basename(file_info["file_upload"])
    ocr_data = ""
    extractions_data = ""
    upload_details = requests.get(endpoint + "/documents/" + file_id, headers=headers)
    if check_response(upload_details):
        # Keep polling till the endpoint finishes processing the document
        if upload_details.json()["processing_status"] == "pending":
            time.sleep(2)
            get_processed_doc(file_info, proc_type, file_type)
        elif upload_details.json()["processing_status"] == "success":
            response_processed = get_details(
                "processed_doc", file_id, proc_type, file_type, file_name
            )
            processed_doc = retreive_processed_file(response_processed)
            if proc_type == "Extractions":
                response_extractions = get_details(
                    "extractions", file_id, proc_type, file_type, file_name
                )
                extractions_data = json.dumps(response_extractions.json())
            response_ocr = get_details("ocr", file_id, proc_type, file_type, file_name)
            ocr_data = json.dumps(response_ocr.json())
            write_to_file_folder(
                file_name,
                proc_type,
                ocr_data.encode(),
                extractions_data.encode(),
                json.dumps(upload_details.json()).encode(),
                processed_doc,
                file_type,
            )
        else:
            write_to_log(
                "Error processing document: {}".format(str(file_name)),
                proc_type,
                file_type,
                "error",
            )
    else:
        write_to_log(
            "Error retreiving upload_details for document: {}".format(str(file_name)),
            proc_type,
            file_type,
            "error",
        )


# Read recipe inputs
input_folder = get_input_names_for_role("File_upload")
output_folder = get_output_names_for_role("Processed_files")
input_handle = dataiku.Folder(input_folder[0])
output_handle = dataiku.Folder(output_folder[0])
input_folder_paths = input_handle.list_paths_in_partition()
output_folder_paths = output_handle.list_paths_in_partition()
logger = logging.getLogger(__name__)
cred = get_recipe_config()["natif_cred"]
usr = cred["login_credentials"]["user"]
pwd = cred["login_credentials"]["password"]
endpoint = "https://apiv3.natif.ai"
error_message = ""
# Bearer token for authentication
bearer = retreive_bearer_token(endpoint, usr, pwd)
if len(bearer) == 0:
    logger.error("Credentials error")
    raise ValueError(
        "Cannot retreive access_token. Please check credentials and try again"
    )
else:
    # Header information to interface with the API
    headers = {
        "accept": "application/json",
        "Authorization": bearer,
    }
    create_uploaded_folder(input_handle, output_handle)
    output_folder_paths = output_handle.list_paths_in_partition()
    file_info = dict()
    doc_type = ""
    for file_path in input_folder_paths:
        if os.path.basename(file_path) in ("error_log.txt", "info_log.txt"):
            continue
        path_list = str(file_path).split(
            "/"
        )  # Example of a file path: [0]/[1]Deep-OCR/[2]Invoice/[3]{file} '[] indicates position in a list'
        if path_list[1] == "Deep-OCR":
            doc_type = "other"
        else:
            doc_type = path_list[2]
        fil_upload_details = upload_files(file_path, doc_type)
        resp_chk = check_response(fil_upload_details)
        if resp_chk == "quota_exceeded":
            write_to_log("Document quota exceeded", path_list[1], doc_type, "error")
            raise ValueError("You have reached your document quota this month!")
        elif resp_chk:
            write_to_log(
                "Success uploading file: {}".format(str(file_path)),
                path_list[1],
                doc_type,
                "info",
            )
            upload_details = fil_upload_details.json()
            file_info["uuid"] = upload_details["uuid"]
            file_info["file_upload"] = file_path
            get_processed_doc(file_info, path_list[1], doc_type)
        else:
            write_to_log(
                "Error uploading file: {}".format(str(file_path)),
                path_list[1],
                doc_type,
                "error",
                output_handle,
            )
