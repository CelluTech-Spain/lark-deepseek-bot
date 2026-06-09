import json

def handler(event, context):
    body = json.loads(event["body"])
    if "challenge" in body:
        return {"statusCode": 200, "body": json.dumps({"challenge": body["challenge"]})}
    return {"statusCode": 200, "body": "ok"}
