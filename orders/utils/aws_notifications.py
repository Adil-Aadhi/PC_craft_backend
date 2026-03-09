import boto3
import json

lambda_client = boto3.client("lambda", region_name="ap-south-1")

def send_push_notification(email, title, message, order_id):

    payload = {
        "email": email,
        "title": title,
        "message": message,
        "order_id": str(order_id)
    }

    lambda_client.invoke(
        FunctionName="send_notification",
        InvocationType="Event",
        Payload=json.dumps(payload)
    )