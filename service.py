from db import insert_batch_request, get_queued_requests

def process_batch_request():

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

    insert_batch_request(
        model_deployment_name="gpt-4.1-batch",
        response_json= structured_output_json,
        instructions="Analyze these images and extract first name, last name, date of birth and address from the images.",
        file_names=["sample_files/2.png"]
    )


if __name__ == "__main__":
    # process_batch_request()
    # print("Batch request processed successfully.")
    response = get_queued_requests("gpt-4.1-batch")
    print(response)