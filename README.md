# OpenAI Batch Document Processing

This project provides a service for batch processing documents using Azure OpenAI and Document Intelligence. It extracts information from documents based on provided schemas and instructions.

## Features

- Process multiple documents in a single API request
- Extract structured information based on custom schemas
- Support for various document formats (PDF, DOCX, PNG, JPG, etc.)
- Integration with Azure OpenAI for intelligent document processing
- Azure Document Intelligence for improved document parsing
- Azure Blob Storage integration for document storage
- SQL Database for tracking processing requests and results

## Prerequisites

- Python 3.10+
- Azure OpenAI account and API key
- Azure Document Intelligence account and API key
- Azure Storage Account
- Azure SQL Database (or local SQL Server)

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd OpenAI_Batch_Document_Processing
   ```

2. Create a virtual environment and activate it:
   ```bash
   python -m venv venv
   # For Windows
   venv\Scripts\activate
   # For Linux/Mac
   source venv/bin/activate
   ```

3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the root directory with the following configuration (replace with your own values):
   ```
   STORAGE_CONNECTION_STRING='DefaultEndpointsProtocol=https;AccountName=your_account_name;AccountKey=your_account_key;EndpointSuffix=core.windows.net'
   OPENAI_BATCH_ENDPOINT=https://your-openai-batch-endpoint.openai.azure.com/
   OPENAI_BATCH_API_KEY=your-openai-batch-api-key
   OPENAI_ENDPOINT=https://your-openai-endpoint.azure.com/models/chat/completions?api-version=
   OPENAI_API_KEY=your-openai-api-key
   OPENAI_API_VERSION=2024-05-01-preview
   SQL_SERVER=your-sql-server.database.windows.net
   SQL_DATABASE=your-database-name
   SQL_USERNAME=your_db_username
   SQL_PASSWORD='your_db_password'
   DOCUMENT_INTELLIGENCE_ENDPOINT=https://your-doc-intel-endpoint.cognitiveservices.azure.com/
   DOCUMENT_INTELLIGENCE_API_KEY=your-doc-intel-api-key
   ```

## Running the Service

Run the service locally:

```bash
# Using Python directly
python api.py

# Alternatively, if using Azure Functions
func start
```

The API will be available at `http://localhost:8000`.

## API Endpoints

### Process Document

```
POST /process_document
```

This endpoint accepts multipart form data with the following parameters:

- `files`: One or more document files to process
- `deployment_name`: The OpenAI deployment name to use (e.g., "gpt-4o", "grok-3")
- `instructions`: Instructions for processing the documents
- `schema`: JSON schema defining the expected output structure

### Check API Status

```
GET /
```

Returns the API status and version information.

## Testing

You can use the included HTTP test files to test the API:

- `test-documentIntelligenece.http`: Tests for Document Intelligence integration
- `test-vision.http`: Tests for vision-based document analysis
- `batch-test.http`: Tests for batch processing scenarios

These files can be executed using the REST Client extension in VS Code or imported into Postman using the included `postman_collection.json` file.

## Docker Support

The project includes a Dockerfile for containerized deployment:

```bash
# Build the Docker image
docker build -t openai-batch-processing .

# Run the Docker container
docker run -p 8000:8000 --env-file .env openai-batch-processing
```

## Project Structure

- `api.py`: Main API entry point and FastAPI setup
- `blob.py`: Azure Blob Storage integration
- `db.py`: Database operations and models
- `documentIntelligence.py`: Azure Document Intelligence integration
- `models.py`: Data models and schemas
- `openai_requests.py`: Integration with Azure OpenAI
- `service.py`: Core business logic

## Example Usage

Refer to the `test-documentIntelligenece.http` file for example API requests, including:
- Basic document processing with schema extraction
- Multiple file processing
- Financial document analysis
- Text document sentiment analysis

## License

[MIT License](LICENSE)
