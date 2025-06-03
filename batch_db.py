# Handles file uploads, Table Storage, and batch logic for the HTTP trigger
import logging
import os
import uuid
from azure.data.tables import TableServiceClient, UpdateMode
from azure.core.exceptions import ResourceNotFoundError
from models import BatchRequestEntity
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Helper to get table client
def get_table_client():
    service = TableServiceClient.from_connection_string(os.environ.get("STORAGE_CONNECTION_STRING"))
    table_client = service.get_table_client(table_name=os.environ.get("TABLE_NAME"))
    # Check if table exists, create if it doesn't
    try:
        table_client.create_table()
    except Exception:
        logging.info("Table already exists or could not be created.")
    return table_client

# Insert a new batch request
def insert_batch_request(model_deployment_name, response_json, instructions, file_names):
    table_client = get_table_client()
    row_key = str(uuid.uuid4())
    entity = BatchRequestEntity(
        partition_key=model_deployment_name,
        row_key=row_key,
        model_deployment_name=model_deployment_name,
        response_json=response_json,
        instructions=instructions,
        status="queued",
        file_names=file_names
    )
    table_client.upsert_entity(mode=UpdateMode.MERGE, entity=entity)
    return row_key

# Get queued requests for a model
def get_queued_requests(model_deployment_name):
    table_client = get_table_client()
    filter_str = f"PartitionKey eq '{model_deployment_name}' and Status eq 'queued'"
    return list(table_client.query_entities(query_filter=filter_str))

# Update status and batch id
def update_requests_to_processing(model_deployment_name, row_keys, batch_id):
    table_client = get_table_client()
    for row_key in row_keys:
        entity = table_client.get_entity(partition_key=model_deployment_name, row_key=row_key)
        entity["Status"] = "processing"
        entity["BatchId"] = batch_id
        table_client.upsert_entity(mode=UpdateMode.MERGE, entity=entity)

# Update status and result
def update_request_status(row_key, status, result=None):
    table_client = get_table_client()
    entity = table_client.get_entity(partition_key=None, row_key=row_key)
    entity["Status"] = status
    if result:
        entity["Result"] = result
    table_client.upsert_entity(mode=UpdateMode.MERGE, entity=entity)
