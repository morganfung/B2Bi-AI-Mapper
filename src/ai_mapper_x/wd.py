# watson discovery api
import os, sys

# TODO: need to restructure the project
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))
import requests
import json
from bs4 import BeautifulSoup
from requests.auth import HTTPBasicAuth
from ai_mapper_x.config import get_config
from logger import logger


config = get_config()


WD_API_KEY = os.getenv("WD_API_KEY")
WD_INSTANCE_ID = config.get("WD").get("INSTANCE_ID")
WD_PROJECT_ID = config.get("WD").get("PROJECT_ID")
VERSION = config.get("WD").get("VERSION")
COLLECTION_ID = config.get("WD").get("COLLECTION_ID")
API_BASE_URL = config.get("WD").get("API_BASE_URL")


url = f"{API_BASE_URL}/instances/{WD_INSTANCE_ID}/v2/projects/{WD_PROJECT_ID}/query?version={VERSION}"


def get_enriched_document(document_id):
    payload = json.dumps(
        {
            "collection_ids": [
                COLLECTION_ID,
            ],
            "query": f"document_id:{document_id}",
        }
    )
    headers = {
        "Content-Type": "application/json",
    }

    response = requests.request(
        "POST",
        url,
        headers=headers,
        data=payload,
        auth=HTTPBasicAuth("apikey", WD_API_KEY),
    )
    response.raise_for_status()
    return response.json()


def get_segment_content(doc, segment_name):

    html = doc.get("html")[0]
    soup = BeautifulSoup(html, "lxml")

    start_tag = None
    for p_tag in soup.find_all("p"):
        span_tag = p_tag.find(
            "span",
            class_=lambda class_name: class_name and class_name.startswith("segment"),
        )
        if span_tag:
            bbox_tag = span_tag.find("bbox")

            if (
                bbox_tag
                and segment_name.lower() in bbox_tag.get_text(strip=True).lower()
            ):
                start_tag = p_tag
                break

    if start_tag:
        # Now, we need to extract all text between this start_tag and the next segment
        text_between_segments = []
        current_tag = start_tag.find_next(
            "p"
        )  # Start from the next <p> tag after the starting one

        while current_tag:
            span_tag = current_tag.find(
                "span",
                class_=lambda class_name: class_name
                and class_name.startswith("segment"),
            )
            if span_tag:
                break  # Found the next segment, stop the loop

            text_between_segments.append(current_tag.get_text(strip=True))

            current_tag = current_tag.find_next("p")

        segment_content = segment_name + "\n" + "\n\n".join(text_between_segments)
        return segment_content
    else:
        logger.warning(f"Returning whole text from WD.")
        res = [p.get_text(strip=True) for p in soup.find_all("p")]
        return "\n".join(res)


def upload_file(file, filename, content_type):  # file: file like object
    upload_url = f"{API_BASE_URL}/instances/{WD_INSTANCE_ID}/v2/projects/{WD_PROJECT_ID}/collections/{COLLECTION_ID}/documents?version={VERSION}"
    files = {"file": (filename, file.read(), content_type)}

    metadata = {"filename": filename, "file_type": content_type}

    response = requests.post(
        upload_url,
        files=files,
        json={"metadata": metadata},
        auth=HTTPBasicAuth("apikey", WD_API_KEY),
    )

    response.raise_for_status()
    return response
