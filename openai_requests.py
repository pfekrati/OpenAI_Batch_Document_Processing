import os
import json
import requests
from dotenv import load_dotenv
from openai import AzureOpenAI
import base64
from mimetypes import guess_type


load_dotenv()

def create_jsonl_and_upload(requests_list):
    # Ensure requests_list is not empty
    if not requests_list:
        raise ValueError("requests_list cannot be empty")
    
    batch_ids = []
    
    for req in requests_list:
        # Get model_deployment_name from each request
        model_deployment_name = req.get("ModelDeploymentName")
        if not model_deployment_name:
            raise ValueError("ModelDeploymentName not found in a request")
        
        # Create JSONL file for this request
        jsonl_filename = f"batch_{model_deployment_name}_{len(batch_ids)}.jsonl"
        with open(jsonl_filename, "w", encoding="utf-8") as f:
            # Write a single JSON object
            f.write(json.dumps({
                "instructions": req["Instructions"],
                "response_json": req["ResponseJson"],
                "file_names": req["FileNames"].split(",")
            }) + "\n")
            
        # Upload to Azure OpenAI batch endpoint
        url = f"{os.environ.get("OPENAI_ENDPOINT")}/openai/deployments/{model_deployment_name}/batch/jobs?api-version=2024-02-15-preview" #2025-01-01-preview
        headers = {
            "api-key": os.environ.get("OPENAI_API_KEY"),
            "Content-Type": "application/jsonl"
        }
        with open(jsonl_filename, "rb") as f:
            response = requests.post(url, headers=headers, data=f)
            
        if response.status_code == 200 or response.status_code == 201:
            batch_id = response.json().get("id")
            batch_ids.append(batch_id)
        else:
            raise Exception(f"Failed to upload batch: {response.status_code} {response.text}")
    
    return batch_ids

def send_request(markdown:str, instructions:str, model_deployment_name:str, structuredOutputJson:dict, model_base_url=None, model_api_version=None, model_api_key=None):
    # Use provided parameters or fall back to environment variables
    api_base = model_base_url or os.getenv("OPENAI_ENDPOINT")
    api_key = model_api_key or os.getenv("OPENAI_API_KEY")
    api_version = model_api_version or os.getenv("OPENAI_API_VERSION")

    client = AzureOpenAI(
        api_key=api_key,
        api_version=api_version,
        base_url=f"{api_base}={api_version}"
    )

    userPrompt = {
        "role": "user",
        "content": f"{instructions}. markdown: {markdown}"
    }

    messages = [{"role": "system", "content": f"You are a helpful assistant that can extract information from a markdown document."}]
    messages.append(userPrompt)

    response = client.beta.chat.completions.parse(
        model=model_deployment_name,
        messages=messages,
        temperature=0,
        response_format={"type": "json_schema", "json_schema": structuredOutputJson}
    )

    return response


def send_request_vision(files: list, instructions: str, model_deployment_name: str, structuredOutputJson: dict):
    api_base = os.getenv("OPENAI_ENDPOINT")
    api_key= os.getenv("OPENAI_API_KEY")
    deployment_name = model_deployment_name
    api_version = os.getenv("OPENAI_API_VERSION")

    client = AzureOpenAI(
        api_key=api_key,  
        api_version=api_version,
        base_url=f"{api_base}/openai/deployments/{deployment_name}"
    )
    
    userPrompt = { "role": "user", "content": [  
                { 
                    "type": "text", 
                    "text": instructions
                }
            ] } 
    
    # Add each file as image content to the prompt
    for file in files:
        userPrompt["content"].append({ 
            "type": "image_url",
            "image_url": {
                "url": local_image_to_data_url(file)
            }
        })

    messages=[{ "role": "system", "content": "You are a helpful assistant." }]
    messages.append(userPrompt)

    response = client.beta.chat.completions.parse(
        model=deployment_name,
        messages=messages,
        temperature=0,
        response_format= { "type": "json_schema","json_schema": structuredOutputJson}
    )
    
    return response
    
def local_image_to_data_url(image_path):
    # Guess the MIME type of the image based on the file extension
    mime_type, _ = guess_type(image_path)
    if mime_type is None:
        mime_type = 'application/octet-stream'  # Default MIME type if none is found

    # Read and encode the image file
    with open(image_path, "rb") as image_file:
        base64_encoded_data = base64.b64encode(image_file.read()).decode('utf-8')

    # Construct the data URL
    return f"data:{mime_type};base64,{base64_encoded_data}"


if __name__ == "__main__":
    # Example usage
    files = ["sample_files/2.png"]  
    instructions = "Analyze these images and extract first name, last name, date of birth and address from the images."
    model_deployment_name = "gpt-4o"
    
    # Example of structured output format
    structured_output_json =  {
            "name": "Information_extract",
            "description": "Extracts personal information from documents",
            "strict": True,
            "schema": {
                "type": "object",
                "properties": {
                    "FirstName": {
                        "type": "string",
                        "description": "The first name of the applicant"
                    },
                    "LastName": {
                        "type": "string",
                        "description": "The last name of the applicant"
                    },
                    "DateOfBirth": {
                        "type": "string",
                        "description": "The birth date of the applicant"
                    },
                    "Address": {
                        "type": "string",
                        "description": "The address of the applicant"
                    }
                },
                "additionalProperties": False,
                "required": ["FirstName", "LastName", "DateOfBirth", "Address"]
            }
        }
    
    # Call the send_request function
    response = send_request(files, instructions, model_deployment_name, structured_output_json)
    print("Response:", response)
    print("Response:", response.choices[0].message.content)