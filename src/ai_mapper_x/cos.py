### Interface to cos
import os
import json
import ibm_boto3
from ibm_botocore.client import Config
from typing import Dict
import sys
from logger import logger


# TODO: check later
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))
from ai_mapper_x.config import get_config


config = get_config()


PROJECT_DIR = os.path.join(os.path.dirname(__file__), "../..")
# MASTER_MXL_PATH = os.path.join(PROJECT_DIR, "data/Map/NBL_Master_850_EDI2FF.mxl")
# TRAINING_DATA_DIR = os.path.join(PROJECT_DIR, "training-data/850_4010")


def get_master_mxl(transaction_type: str) -> str:
    """Returns master mxl file.

    Returns:
        str: file path
    """
    # Add conditonals for expanding transaction type compatibility. Currently handling 850 and 810 EDI Docs.
    MASTER_MXL_PATH = PROJECT_DIR

    # Cannot use format string as end of file name is not consistent. Idea: truncate after NBL_Master_XXX
    if transaction_type == "850":
        MASTER_MXL_PATH = os.path.join(PROJECT_DIR, "data/Map/NBL_Master_850_EDI2FF.mxl")
    elif transaction_type == "810":
        MASTER_MXL_PATH = os.path.join(PROJECT_DIR, "data/Map/NBL_Master_810_FF2EDI.mxl")

    return MASTER_MXL_PATH


def get_complex_rule_config(transaction_type: str):
    TRAINING_DATA_DIR = os.path.join(PROJECT_DIR, f"training-data/{transaction_type}_4010")
    return json.load(open(f"{TRAINING_DATA_DIR}/complex_rule.json"))


def get_simple_rule_data(transaction_type: str):
    TRAINING_DATA_DIR = os.path.join(PROJECT_DIR, f"training-data/{transaction_type}_4010")
    return json.load(open(f"{TRAINING_DATA_DIR}/simple_rule.json"))

def get_monitorpro_data(transaction_type: str):
    TRAINING_DATA_DIR = os.path.join(PROJECT_DIR, f"training-data/{transaction_type}_4010")
    return json.load(open(f"{TRAINING_DATA_DIR}/monitorpro.json"))


COS_API_KEY = os.environ.get("COS_API_KEY")
cos_client = ibm_boto3.client(
    "s3",
    ibm_api_key_id=COS_API_KEY,
    ibm_service_instance_id=config.get("COS").get("COS_INSTANCE_CRN"),
    config=Config(signature_version="oauth"),
    endpoint_url=config.get("COS").get("COS_ENDPOINT"),
    verify=False
)


BUCKET_NAME = config.get("COS").get("BUCKET_NAME")


def create_object(object_key: str, file_content: str, bucket_name: str = BUCKET_NAME)-> None:
    logger.info(f"Creating new object: {object_key}")
    try:
        cos_client.put_object(Bucket=bucket_name, Key=object_key, Body=file_content)
        logger.info("Object: {0} created!".format(object_key))
    except Exception as e:
        logger.error("Unable to create file: {0}".format(e))
        raise Exception("Unable to store map file to object storage.")


def get_object(
    object_key: str,
    bucket_name: str = BUCKET_NAME,
)-> Dict:
    logger.info(f"Retrieving item from bucket: {bucket_name}, key: {object_key}")
    try:
        return cos_client.get_object(Bucket=bucket_name, Key=object_key)
    except Exception as e:
        logger.error("Unable to retrieve file contents: {0}".format(e))
        raise Exception("Unable to retrieve map file contents.")