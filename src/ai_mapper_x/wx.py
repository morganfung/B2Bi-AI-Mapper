##  Watson X

import os, sys
#TODO: need to restructure the project
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

from ai_mapper_x.config import get_config
from ibm_watsonx_ai.foundation_models import ModelInference


config = get_config()


WX_PROJECT_ID = config.get("WX").get("PROJECT_ID")
API_BASE_URL = config.get("WX").get("API_BASE_URL")
WX_API_KEY = os.environ.get("WX_API_KEY")


model_id = "ibm/granite-3-8b-instruct"


parameters = {
    "decoding_method": "greedy",
    "max_new_tokens": 1000,
    "min_new_tokens": 0,
    "repetition_penalty": 1,
}


credentials = {"url": API_BASE_URL, "apikey": WX_API_KEY}


model_inference = ModelInference(
    model_id=model_id,
    params=parameters,
    credentials=credentials,
    project_id=WX_PROJECT_ID,
)


def wx_call(prompt_input):
    return model_inference.generate_text(prompt=prompt_input)


async def wx_call_async(prompt_input):
    result = await model_inference.agenerate(prompt=prompt_input)
    return result.get("results")[0].get("generated_text")