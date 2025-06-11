import os
import json


def get_config():
    config = json.load(
        open(os.path.join(os.path.dirname(__file__), "config/config.json"))
    )
    return config
