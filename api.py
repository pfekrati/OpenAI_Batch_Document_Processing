from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from typing import List, Dict, Any
import json
import tempfile
import os
from pydantic import BaseModel
import shutil
from openai_requests import send_request
import uvicorn
from db import insert_batch_request, get_queued_requests, update_requests_to_processing, initialize_database
from blob import upload_multiple_files, create_container
from documentIntelligence import process_document_to_markdown

# Define response models for better documentation
class ProcessingResponse(BaseModel):
    """Response model for document processing results"""
    # This is a generic response model - adapt based on your actual schema
    result: Dict[str, Any]

class ErrorResponse(BaseModel):
    """Error response model"""
    detail: str

app = FastAPI(
    title="Document Processing API", 
    description="API for processing documents using Azure OpenAI services",
    version="1.0.0",
    docs_url="/docs",  # Default Swagger UI endpoint
    redoc_url="/redoc"  # Alternative documentation UI
)

# Create a temporary directory to store uploaded files
TEMP_DIR = os.path.join(tempfile.gettempdir(), "document_processing")
os.makedirs(TEMP_DIR, exist_ok=True)

@app.post(
    "/process_document", 
    summary="Process documents with Azure OpenAI",
    description="Upload documents to be processed by Azure OpenAI services according to provided instructions and schema",
    response_model=Dict[str, Any],
    responses={
        200: {"description": "Successfully processed documents", "model": ProcessingResponse},
        400: {"description": "Bad request", "model": ErrorResponse},
        500: {"description": "Server error", "model": ErrorResponse}
    }
)
async def process_document(
    files: List[UploadFile] = File(..., description="Documents to process"),
    deployment_name: str = Form(..., description="Azure OpenAI model deployment name"),
    instructions: str = Form(..., description="Instructions for processing the documents"),
    schema: str = Form(..., description="JSON schema for structured output")
):
    # Validate inputs
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")
    
    try:
        # Parse the JSON schema
        json_schema = json.loads(schema)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON schema")
    
    # Save uploaded files temporarily
    temp_file_paths = []
    try:
        for file in files:
            file_path = os.path.join(TEMP_DIR, file.filename)
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            temp_file_paths.append(file_path)
        
        # conver files into markdown
        markdown = ""
        for file_path in temp_file_paths:
            markdown += process_document_to_markdown(file_path) + "\n\n"

        # Process the documents
        response = send_request(
            markdown=markdown,
            instructions=instructions,
            model_deployment_name=deployment_name,
            structuredOutputJson=json_schema
        )
        
        # Parse the response
        if hasattr(response, 'choices') and response.choices:
            result = json.loads(response.choices[0].message.content)
            return JSONResponse(content=result)
        else:
            return JSONResponse(content={
                "response": str(response)
            })
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing documents: {str(e)}")
    finally:
        # Clean up temporary files
        for file_path in temp_file_paths:
            if os.path.exists(file_path):
                os.remove(file_path)


@app.post(
    "/queue_document", 
    summary="Queue document for batch processing with Azure OpenAI",
    description="Upload documents to be processed by Azure OpenAI services according to provided instructions and schema",
    response_model=Dict[str, Any],
    responses={
        200: {"description": "Successfully processed documents", "model": ProcessingResponse},
        400: {"description": "Bad request", "model": ErrorResponse},
        500: {"description": "Server error", "model": ErrorResponse}
    }
)
async def process_document(
    files: List[UploadFile] = File(..., description="Documents to process"),
    deployment_name: str = Form(..., description="Azure OpenAI model deployment name"),
    instructions: str = Form(..., description="Instructions for processing the documents"),
    schema: str = Form(..., description="JSON schema for structured output")
):
    # Validate inputs
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")
    
    try:
        # Parse the JSON schema
        json_schema = json.loads(schema)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON schema")
    
    # Save uploaded files temporarily
    temp_file_paths = []
    try:
        # Define a container name for document processing
        container_name = "document-processing"

        # Save uploaded files temporarily, then upload to blob storage
        for file in files:
            file_path = os.path.join(TEMP_DIR, file.filename)
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            temp_file_paths.append(file_path)

        # Upload files to blob storage
        blob_url_dict = upload_multiple_files(container_name, temp_file_paths)

        # Check if any uploads failed
        if None in blob_url_dict.values():
            raise HTTPException(status_code=500, detail="Failed to upload some files to blob storage")
            
        # Insert the batch request into the database
        request_id = insert_batch_request(
            model_deployment_name=deployment_name,
            instructions=instructions,
            response_json_schema=json_schema,
            file_names=",".join(blob_url_dict.values())
        )

        return JSONResponse(content={
            "message": "Documents queued for processing",
            "request_id": request_id
        })
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing documents: {str(e)}")
    finally:
        # Clean up temporary files
        for file_path in temp_file_paths:
            if os.path.exists(file_path):
                os.remove(file_path)

@app.get(
    "/",
    summary="API Status",
    description="Check if the Document Processing API is running",
    response_model=Dict[str, str]
)
async def root():
    return {"message": "Document Processing API is running. Use /process_document endpoint to process documents."}

# Custom OpenAPI schema configuration (optional)
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    
    # Add additional info to the OpenAPI schema if needed
    openapi_schema["info"]["x-logo"] = {
        "url": "https://fastapi.tiangolo.com/img/logo-margin/logo-teal.png"
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

if __name__ == "__main__":
    initialize_database() # Ensure the database is initialized
    create_container("document-processing")  # Ensure the blob container exists
    uvicorn.run(app, host="0.0.0.0", port=8000)