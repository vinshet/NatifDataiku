# import the classes for accessing DSS objects from the recipe
import dataiku

# Import the helpers for custom recipes
from dataiku.customrecipe import get_recipe_config, get_output_names_for_role
import os
import logging
import shutil

logger = logging.getLogger(__name__)


# Clears the output folder
def clear_output_folder():
    list_dir = os.listdir(path_to_folder)
    for filename in list_dir:
        file_path = os.path.join(path_to_folder, filename)
        # If the element is a file
        if os.path.isfile(file_path) or os.path.islink(file_path):
            logger.info("deleting file: {}".format(file_path))
            os.unlink(file_path)
        # In case is a folder
        elif os.path.isdir(file_path):
            logger.info("deleting folder: {}".format(file_path))
            shutil.rmtree(file_path)
    logger.info("Cleared the output folder")


def create_default_files(proc_type, doc_type):
    writer = ""
    if proc_type == "Deep-OCR":
        writer = "/Deep-OCR/"
    else:
        writer = "/Extractions/{}/".format(doc_type)
    with folder_structure.get_writer(writer + "error_log.txt") as w:
        w.write("No errors recorded")
    with folder_structure.get_writer(writer + "info_log.txt") as w:
        w.write("No documents processed")


# For outputs, the process is the same:
output_handle = get_output_names_for_role("Output")
ocr = get_recipe_config()["DeepOCR"]
extractions = get_recipe_config()["Extractions"]
invoice = get_recipe_config()["Invoices"]
order_confirmation = get_recipe_config()["Order_confirmation"]
delivery_note = get_recipe_config()["Delivery_note"]
clr_fld = get_recipe_config()["fold_clear"]
dir_set = set()
# Write recipe outputs
folder_structure = dataiku.Folder(output_handle[0])
path_to_folder = folder_structure.get_path()
if clr_fld:
    clear_output_folder()

# Folder creation for Extractions
if extractions:
    # Sub-folder creation for Extractions
    if invoice:
        create_default_files("Extractions", "Invoice")
    if order_confirmation:
        create_default_files("Extractions", "Order_confirmation")
    if delivery_note:
        create_default_files("Extractions", "Delivery_note")

# Folder creation for Deep-OCR
if ocr:
    create_default_files("Deep-OCR", "other")
