import boto3
from django.conf import settings
from datetime import datetime

COMPONENTS = [
    "cpu",
    "motherboard",
    "ram",
    "gpu",
    "storage",
    "psu",
    "case",
    "case_fan",   # ✅ changed
    "cooler",
]

dynamodb = boto3.resource(
    "dynamodb",
    region_name=settings.DYNAMO_AWS_REGION,
    aws_access_key_id=settings.DYNAMO_AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.DYNAMO_AWS_SECRET_ACCESS_KEY,
)

table = dynamodb.Table(settings.DYNAMODB_TABLE_NAME)


def create_order_progress(order_id):
    item = {
        "order_id": str(order_id),
        "progress": 0,
        "updated_at": datetime.utcnow().isoformat(),
    }

    for comp in COMPONENTS:
        item[comp] = False

    table.put_item(Item=item)


def get_progress(order_id):
    response = table.get_item(
        Key={"order_id": str(order_id)}
    )
    return response.get("Item", {})


def update_component(order_id, component_name):
    if component_name not in COMPONENTS:
        raise ValueError("Invalid component name")

    try:
        # ✅ Use ExpressionAttributeNames to avoid reserved keyword issue
        response = table.update_item(
            Key={"order_id": str(order_id)},
            UpdateExpression="SET #comp = :val, updated_at = :time",
            ExpressionAttributeNames={
                "#comp": component_name
            },
            ExpressionAttributeValues={
                ":val": True,
                ":time": datetime.utcnow().isoformat(),
            },
            ReturnValues="ALL_NEW",
        )

        item = response["Attributes"]

        verified_count = sum(1 for comp in COMPONENTS if item.get(comp))
        progress = int((verified_count / len(COMPONENTS)) * 100)

        # ✅ Update progress safely
        table.update_item(
            Key={"order_id": str(order_id)},
            UpdateExpression="SET #progress = :p",
            ExpressionAttributeNames={
                "#progress": "progress"
            },
            ExpressionAttributeValues={":p": progress},
        )

        return progress

    except Exception as e:
        raise Exception(str(e))