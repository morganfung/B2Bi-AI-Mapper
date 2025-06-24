# API interface for Watson Assistant

# for loading environment variables from .env file
from dotenv import load_dotenv

load_dotenv()

from logger import logger
from fastapi import FastAPI, Depends, UploadFile
from starlette_context import context
from fastapi.responses import JSONResponse
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import traceback
from pydantic import BaseModel
import json
import os
import cos
import wd
from main import generate_map_file
from middlewares import TransactionIDMiddleware
import auth


app = FastAPI(title="AI-Mapper")


# Not sure, add CORS middleware to allow cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Add TransactionID middleware
app.add_middleware(TransactionIDMiddleware)


# Error response object class
class ErrorResponse(BaseModel):
    message: str
    transaction_id: str


# Root endpoint for API
@app.get("/")
async def root():
    return "Hello, AI Mapper!"


# Test authentication endpoint
@app.get("/test")
async def test_endpoint(user=Depends(auth.get_auth_method)):
    return JSONResponse(content={"mxl_id": "0d734334-73e2-49b1-b6df-ce4f92770eab"})
                        

# Generate map file end point
@app.get("/map/generate/{transaction_type}/{document_id}")
async def generate(
    transaction_type: str,
    document_id: str,
    account_number: str = "",
    codelist_name: str = "",
    user=Depends(auth.get_auth_method)
):
    try:
        mxl_id = await generate_map_file(transaction_type, document_id, account_number, codelist_name)
        signed_url = auth.create_signed_url(mxl_id, expiry_seconds=600)
        return JSONResponse(content={"mxl_url": signed_url, "transaction_id": context.transcation_id})
    except Exception as e:
        logger.error(traceback.format_exc())
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                message=str(e), transaction_id=context.transaction_id
            ).dict()
        )

# was: @app.get(/map/download/{mxl_id})
@app.get("/map/download/{transaction_type}/{mxl_id}")
def download_file(transaction_type: str, mxl_id: str, _=Depends(auth.verify_signed_link)):
    try:
        resp = cos.get_object(f"{transaction_type}/generated_mxl/{mxl_id}.mxl")
        return StreamingResponse(
            resp.get("Body"),
            media_type="application/xml",
            headers={"Content-Disposition": f"attachment; filename={mxl_id}.mxl"},
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                message=str(e), transaction_id=context.transaction_id
            ).dict(),
        )


@app.post("/spec/upload/")
def upload_file(file: UploadFile, user=Depends(auth.get_auth_method)):
    """
    Endpoint to handle implementation guide file uploads.

    Args:
        file: The uploaded file object.
    """
    try:
        filename = file.filename
        content_type = file.content_type

        resp = wd.upload_file(file.file, filename, content_type)
        return resp.json()
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                message=str(e), transaction_id=context.transaction_id
            ).dict(),
        )


def custom_openapi():
    """OpenAPI Spec for API Docs

    Returns:
        Dict: return openai spec dict
    """

    openapi_path = os.path.join(os.path.dirname(__file__), "./openapi.json")
    with open(openapi_path) as f:
        custom_openapi = json.load(f)
    return custom_openapi


app.openapi = custom_openapi

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)