from azure.data.tables import TableEntity
from datetime import datetime

class BatchRequestEntity(TableEntity):
    def __init__(self, partition_key, row_key, model_deployment_name, response_json, instructions, status, file_names, batch_id=None, result=None):
        super().__init__()
        self["PartitionKey"] = partition_key
        self["RowKey"] = row_key
        self["ModelDeploymentName"] = model_deployment_name
        self["ResponseJson"] = response_json
        self["Instructions"] = instructions
        self["Status"] = status
        self["FileNames"] = ",".join(file_names)
        self["BatchId"] = batch_id or ""
        self["Result"] = result or ""
        self["Created"] = datetime.utcnow().isoformat()
