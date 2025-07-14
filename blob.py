import os
import logging
from dotenv import load_dotenv
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
from azure.core.exceptions import ResourceNotFoundError, ResourceExistsError

# Initialize logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def get_blob_service_client():
    """
    Create a blob service client using connection string from environment variables.
    
    Returns:
        BlobServiceClient: The blob service client for Azure operations
    """
    connection_string = os.getenv("STORAGE_CONNECTION_STRING")
    if not connection_string:
        raise ValueError("STORAGE_CONNECTION_STRING environment variable not set")
    
    try:
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        return blob_service_client
    except Exception as e:
        logger.error(f"Error connecting to Azure Blob Storage: {str(e)}")
        raise

def create_container(container_name):
    """
    Create a new container in Azure Blob Storage.
    
    Args:
        container_name (str): Name of the container to create
        
    Returns:
        ContainerClient: The container client for the created container
    """
    blob_service_client = get_blob_service_client()
    try:
        container_client = blob_service_client.create_container(container_name)
        logger.info(f"Container {container_name} created successfully")
        return container_client
    except ResourceExistsError:
        logger.info(f"Container {container_name} already exists")
        return blob_service_client.get_container_client(container_name)
    except Exception as e:
        logger.error(f"Error creating container {container_name}: {str(e)}")
        raise

def upload_file(container_name, file_path, blob_name=None):
    """
    Upload a file to Azure Blob Storage.
    
    Args:
        container_name (str): Name of the container
        file_path (str): Path to the file to upload
        blob_name (str, optional): Name to give the blob in storage. If None, uses file name
        
    Returns:
        str: URL of the uploaded blob
    """
    # If blob_name is not specified, use the file name
    if blob_name is None:
        blob_name = os.path.basename(file_path)
    
    blob_service_client = get_blob_service_client()
    
    # Ensure container exists
    try:
        container_client = blob_service_client.get_container_client(container_name)
        if not container_client.exists():
            container_client = create_container(container_name)
    except Exception:
        container_client = create_container(container_name)
    
    # Upload file
    try:
        blob_client = blob_service_client.get_blob_client(
            container=container_name, blob=blob_name
        )
        
        with open(file_path, "rb") as data:
            blob_client.upload_blob(data, overwrite=True)
        
        logger.info(f"File {file_path} uploaded to {container_name}/{blob_name}")
        return blob_client.url
    except Exception as e:
        logger.error(f"Error uploading file {file_path}: {str(e)}")
        raise

def upload_multiple_files(container_name, file_paths):
    """
    Upload multiple files to Azure Blob Storage.
    
    Args:
        container_name (str): Name of the container
        file_paths (list): List of file paths to upload
        
    Returns:
        dict: Dictionary mapping file paths to their URLs in blob storage
    """
    results = {}
    for file_path in file_paths:
        try:
            url = upload_file(container_name, file_path)
            results[file_path] = url
        except Exception as e:
            logger.error(f"Failed to upload {file_path}: {str(e)}")
            results[file_path] = None
    
    return results

def download_file(container_name, blob_name, download_path):
    """
    Download a file from Azure Blob Storage.
    
    Args:
        container_name (str): Name of the container
        blob_name (str): Name of the blob in storage
        download_path (str): Path where the file will be saved
        
    Returns:
        str: Path to the downloaded file
    """
    blob_service_client = get_blob_service_client()
    
    try:
        # Make sure the download directory exists
        os.makedirs(os.path.dirname(os.path.abspath(download_path)), exist_ok=True)
        
        blob_client = blob_service_client.get_blob_client(
            container=container_name, blob=blob_name
        )
        
        with open(download_path, "wb") as download_file:
            download_file.write(blob_client.download_blob().readall())
            
        logger.info(f"Downloaded {blob_name} to {download_path}")
        return download_path
    except ResourceNotFoundError:
        logger.error(f"Blob {blob_name} not found in container {container_name}")
        raise
    except Exception as e:
        logger.error(f"Error downloading {blob_name}: {str(e)}")
        raise

def list_blobs(container_name, name_starts_with=None):
    """
    List all blobs in a container.
    
    Args:
        container_name (str): Name of the container
        name_starts_with (str, optional): Filter blobs that start with this prefix
        
    Returns:
        list: List of blob names in the container
    """
    blob_service_client = get_blob_service_client()
    
    try:
        container_client = blob_service_client.get_container_client(container_name)
        blob_list = container_client.list_blobs(name_starts_with=name_starts_with)
        
        return [blob.name for blob in blob_list]
    except ResourceNotFoundError:
        logger.error(f"Container {container_name} not found")
        raise
    except Exception as e:
        logger.error(f"Error listing blobs in container {container_name}: {str(e)}")
        raise

def delete_blob(container_name, blob_name):
    """
    Delete a blob from Azure Blob Storage.
    
    Args:
        container_name (str): Name of the container
        blob_name (str): Name of the blob to delete
        
    Returns:
        bool: True if deletion was successful, False otherwise
    """
    blob_service_client = get_blob_service_client()
    
    try:
        blob_client = blob_service_client.get_blob_client(
            container=container_name, blob=blob_name
        )
        blob_client.delete_blob()
        logger.info(f"Deleted blob {blob_name} from container {container_name}")
        return True
    except ResourceNotFoundError:
        logger.warning(f"Blob {blob_name} not found in container {container_name}")
        return False
    except Exception as e:
        logger.error(f"Error deleting blob {blob_name}: {str(e)}")
        raise

def get_blob_sas_url(container_name, blob_name, expiry_hours=1):
    """
    Generate a Shared Access Signature (SAS) URL for a blob with read permissions.
    
    Args:
        container_name (str): Name of the container
        blob_name (str): Name of the blob
        expiry_hours (int): Number of hours until the SAS token expires
        
    Returns:
        str: SAS URL for the blob
    """
    from datetime import datetime, timedelta
    from azure.storage.blob import generate_blob_sas, BlobSasPermissions
    
    account_name = os.getenv("AZURE_STORAGE_ACCOUNT_NAME")
    account_key = os.getenv("AZURE_STORAGE_ACCOUNT_KEY")
    
    if not account_name or not account_key:
        raise ValueError("Azure storage account name or key environment variables not set")
    
    try:
        # Generate SAS token
        sas_token = generate_blob_sas(
            account_name=account_name,
            container_name=container_name,
            blob_name=blob_name,
            account_key=account_key,
            permission=BlobSasPermissions(read=True),
            expiry=datetime.utcnow() + timedelta(hours=expiry_hours)
        )
        
        # Construct the full URL
        sas_url = f"https://{account_name}.blob.core.windows.net/{container_name}/{blob_name}?{sas_token}"
        logger.info(f"Generated SAS URL for {container_name}/{blob_name}")
        return sas_url
    except Exception as e:
        logger.error(f"Error generating SAS URL for {blob_name}: {str(e)}")
        raise

if __name__ == "__main__":
    # Example usage
    try:
        # Set these values for testing
        test_container = "documents"
        test_file = "sample_files/2.png"  # Matches the path in openai_requests.py
        
        # Create container if it doesn't exist
        create_container(test_container)
        
        # Upload a test file
        blob_url = upload_file(test_container, test_file)
        print(f"Uploaded file URL: {blob_url}")
        
        # List all blobs in the container
        print("Blobs in container:", list_blobs(test_container))
        
        # Download the file
        download_path = os.path.join("downloads", os.path.basename(test_file))
        downloaded_file = download_file(test_container, os.path.basename(test_file), download_path)
        print(f"Downloaded file to: {downloaded_file}")
        
        # Generate SAS URL
        sas_url = get_blob_sas_url(test_container, os.path.basename(test_file))
        print(f"SAS URL: {sas_url}")
        
    except Exception as e:
        print(f"Error in example: {str(e)}")