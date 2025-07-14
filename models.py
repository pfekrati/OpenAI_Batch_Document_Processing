from datetime import datetime

class BatchRequestEntity():
    def __init__(self, model_deployment_name, response_json_schema, instructions, status, file_names, id=None, batch_id=None, result=None):
        super().__init__()
        self["Id"] = id or ""
        self["ModelDeploymentName"] = model_deployment_name
        self["ResponseJsonSchema"] = str(response_json_schema)
        self["Instructions"] = instructions
        self["Status"] = status
        self["FileNames"] = ",".join(file_names)
        self["BatchId"] = batch_id or ""
        self["Result"] = result or ""
        self["Created"] = datetime.utcnow().isoformat()

