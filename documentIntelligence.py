import os
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential
from dotenv import load_dotenv

load_dotenv()

def process_document_to_markdown(file_path):
    """
    Send a document to Azure Document Intelligence and return the raw result.
    
    Args:
        file_path (str): Path to the document file to process
    
    Returns:
        dict: Raw result from Document Intelligence
    """
    document_analysis_client = DocumentAnalysisClient(
        endpoint=os.getenv("DOCUMENT_INTELLIGENCE_ENDPOINT"), 
        credential=AzureKeyCredential(os.getenv("DOCUMENT_INTELLIGENCE_API_KEY"))
    )
    
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    with open(file_path, "rb") as f:
        document_content = f.read()
    
    poller = document_analysis_client.begin_analyze_document(
        "prebuilt-layout",
        document_content
    )
    result = poller.result()
    
    # Return the raw result as a dictionary
    return result.content
