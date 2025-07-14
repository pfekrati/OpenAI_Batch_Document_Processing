# Handles file uploads, SQL Database, and batch logic for the HTTP trigger
import logging
import os
import uuid
import pyodbc
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Helper to get SQL connection
def get_sql_connection():
    server = os.environ.get("SQL_SERVER")
    database = os.environ.get("SQL_DATABASE")
    username = os.environ.get("SQL_USERNAME")
    password = os.environ.get("SQL_PASSWORD")
    driver = "{ODBC Driver 17 for SQL Server}"
    
    connection_string = f"DRIVER={driver};SERVER={server};DATABASE={database};UID={username};PWD={password}"
    return pyodbc.connect(connection_string)

# Initialize the database table if it doesn't exist
def initialize_database():
    conn = get_sql_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
        IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'BatchRequest')
        BEGIN
            CREATE TABLE BatchRequest (
                Id NVARCHAR(50) PRIMARY KEY,
                ModelDeploymentName NVARCHAR(100) NOT NULL,
                ResponseJsonSchema NVARCHAR(MAX) NOT NULL,
                Instructions NVARCHAR(MAX) NOT NULL,
                Status NVARCHAR(50) NOT NULL,
                FileNames NVARCHAR(MAX) NOT NULL,
                BatchId NVARCHAR(50),
                Result NVARCHAR(MAX),
                Created DATETIME NOT NULL
            )
        END
        """)
        conn.commit()
    except Exception as e:
        logging.error(f"Error initializing database: {str(e)}")
    finally:
        cursor.close()
        conn.close()

# Insert a new batch request
def insert_batch_request(model_deployment_name, response_json_schema, instructions, file_names):
    conn = get_sql_connection()
    cursor = conn.cursor()
    id = str(uuid.uuid4())
    
    try:
        cursor.execute("""
        INSERT INTO BatchRequest (Id, ModelDeploymentName, ResponseJsonSchema, Instructions, Status, FileNames, Created)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (id, model_deployment_name, str(response_json_schema), instructions, "queued", file_names, datetime.now()))
        conn.commit()
    finally:
        cursor.close()
        conn.close()
    
    return id

# Get queued requests for a model
def get_queued_requests():
    conn = get_sql_connection()
    cursor = conn.cursor()
    results = []
    
    try:
        cursor.execute("""
        SELECT * FROM BatchRequest 
        WHERE Status = 'queued'
        """)
        
        columns = [column[0] for column in cursor.description]
        for row in cursor.fetchall():
            entity = {}
            for i, value in enumerate(row):
                entity[columns[i]] = value
            results.append(entity)
    finally:
        cursor.close()
        conn.close()
    
    return results

# Update status and batch id
def update_requests_to_processing(ids, batch_id):
    if not ids:
        return
        
    conn = get_sql_connection()
    cursor = conn.cursor()
    
    try:
        # Create a string with the right number of parameter placeholders
        placeholders = ','.join(['?' for _ in ids])
        
        # Build query using these placeholders
        query = f"""
        UPDATE BatchRequest
        SET Status = 'processing', BatchId = ?
        WHERE Id IN ({placeholders})
        """
        
        # First parameter is batch_id, followed by all the ids
        params = [batch_id] + ids
        
        cursor.execute(query, params)
        conn.commit()
    finally:
        cursor.close()
        conn.close()

# Update status and result
def update_request_status(id, status, result=None):
    conn = get_sql_connection()
    cursor = conn.cursor()
    
    try:
        if result:
            cursor.execute("""
            UPDATE BatchRequest
            SET Status = ?, Result = ?
            WHERE Id = ?
            """, (status, result, id))
        else:
            cursor.execute("""
            UPDATE BatchRequest
            SET Status = ?
            WHERE Id = ?
            """, (status, id))
        conn.commit()
    finally:
        cursor.close()
        conn.close()
