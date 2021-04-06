

# Access the parameters that end-users filled in using webapp config
# For example, for a parameter called "input_dataset"
# input_dataset = get_webapp_config()["input_dataset"]
from dataiku.customwebapp import get_webapp_config
import dataiku
import pandas as pd
from flask import request
from flask import render_template,url_for
from flask import Flask
import logging
import requests
logger = logging.getLogger(__name__)
config = get_webapp_config()
project_key = dataiku.default_project_key()
client = dataiku.api_client()
def retreive_bearer_token(usr,pwd):
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
endpoint = "https://apiv3.natif.ai"

def get_output_folder(config, client, project_key):
    output_managed_id = config.get('output_managed_folder', None) 
    project = client.get_project(project_key)
    if output_managed_id:
        output_folder_dss = project.get_managed_folder(output_managed_id)
    else:
        raise ValueError("The output folder parameter is missing. Select one from the setting of the web app")
    output_folder = dataiku.Folder(output_folder_dss.get_definition()['name'], project_key=project_key)
    return output_folder

def document_update(file_id,output_handle,config):
    cred = config.get('natif_cred_web', None)
    usr=cred["login_credentials"]["user"]
    pwd=cred["login_credentials"]["password"]
    bearer = retreive_bearer_token(usr,pwd)
    headers = {
        "accept": "application/json",
        "Authorization": bearer,
    }
    output_folder_paths=output_handle.list_paths_in_partition()
    e_id=''
    e_doc_type=''
    update=False
    for paths in output_folder_paths:
        if "upload_details.json" in paths:
            with output_handle.get_download_stream(paths) as f:
                t = f.read()
                e_id = json.loads(t)["uuid"]
                e_doc_type= json.loads(t)["document_type"]
                if e_id == file_id:
                    update=True
                    ocr_data=requests.get(endpoint + "/documents/" + e_id + "/ocr?include_raw_types=false", headers=headers)
                    with output_handle.get_writer(os.path.dirname(paths) + "/ocr_data.json") as w:
                        w.write(json.dumps(ocr_data.json()))
                    if e_doc_type != 'other':
                        extractions_data = requests.get(endpoint + "/documents/" + e_id + "/extractions", headers=headers)
                        with output_handle.get_writer(os.path.dirname(paths) + "/ocr_data.json") as w:
                            w.write(json.dumps(extractions_data.json()))
    if update:
        logger.info("Success")
    else:
        logger.info("Fail")
                    
            
    
@app.route('/extract_id',methods=['GET', 'POST'])
def get_id():
    url_string = str(request.args.get("backend_url"))
    logger.info(project_key)
    return json.dumps({"status": "ok", "backend_url": url_string})

@app.route('/update_document',methods=['GET', 'POST'])
def update_document():
    file_id = str(request.args.get("uuid"))
    #implement update function here
    output_folder_handle=get_output_folder(config, client, project_key)
    document_update(file_id,output_folder_handle,config)
    #tmp=output_handle.list_paths_in_partition()
    #logger.info(tmp)
    return json.dumps({"status": "ok", "uuid": file_id})


