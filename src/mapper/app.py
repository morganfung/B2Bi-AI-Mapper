# API interface for Watson Assistant

# for loading environment variables from .env file
from dotenv import load_dotenv

load_dotenv()

from logger import logger
from fastapi import FastAPI, Depends
from starlette_context import context
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
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
                        


@app.get("/map/generate/{document_id}")
async def generate(
    document_id: str,
    account_number: str = "",
    codelist_name: str = "",
    user=Depends(auth.get_auth_method)
):
    try:
        mxl_id = await generate_map_file(document_id, account_number, codelist_name)
        signed_url = auth.create_signed_url(mxl_id, expiry_seconds=600)
        return JSONResponse(content={"mxl_url": signed_url, "transaction_id": context.transcation_id})
    except Exception as e:
        logger.error(traceback.format_exc())
