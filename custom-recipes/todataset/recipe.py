import dataiku
from dataiku.customrecipe import get_input_names_for_role, get_recipe_config, get_output_names_for_role
import pandas as pd
import os

input_folder = get_input_names_for_role("Processed_files")
output_dataset = get_output_names_for_role("Collated_dataset")
# Read recipe inputs
file_names = list()
process_type = list()
data = list()
input_handle = dataiku.Folder(input_folder[0])
findataset = dataiku.Dataset(output_dataset[0])
input_paths = input_handle.list_paths_in_partition()
# Importing the parameters
delete_dataset = get_recipe_config()["delete_dataset"]
# Extracts the data from all the ocr_data.json/extractions_data.json files and combines that into a dataset
for path in input_paths:
    if path.split("/")[1] == "Processed_files":
        if os.path.basename(path) in ("ocr_data.json", "extractions_data.json"):
            with input_handle.get_download_stream(path) as f:
                t = str(f.read())
                data.append(t)
                if os.path.basename(path) == "ocr_data.json":
                    process_type.append("Deep-OCR")
                    file_names.append(os.path.basename(os.path.dirname(path)))
                else:
                    process_type.append("Extractions (" + path.split("/")[3] + ")")
                    file_names.append(os.path.basename(os.path.dirname(path)))


fin = {"File_names": file_names, "Process type": process_type, "Content": data}
df = pd.DataFrame(fin)
findataset.write_with_schema(df, dropAndCreate=delete_dataset)
