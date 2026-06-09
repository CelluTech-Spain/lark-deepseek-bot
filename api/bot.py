import json
import os
import requests
from http.server import BaseHTTPRequestHandler

DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY")
LARK_APP_ID = os.environ.get("LARK_APP_ID")
LARK_APP_SECRET = os.environ.get("LARK_APP_SECRET")

def get_tenant_access_token():
    resp = requests.post(
        "https://open.larksuite.com/open-apis/auth/v3/tenant_access_token/internal",
        json={"app_id": LARK_APP_ID, "app_secret": LARK_APP_SECRET}
    )
    return resp.json()["tenant_access_token"]

def send_message_to_lark(chat_id, text):
    token = get_tenant_access_token()
    payload = {
        "receive_id": chat_id,
        "msg_type": "text",
        "content": json.dumps({"text": text})
    }
    requests.post(
        "https://open.larksuite.com/open-apis/im/v1/messages?receive_id_type=chat_id",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        },
        json=payload
    )

def handler(event, context):
    body = json.loads(event["body"])
    
    # Vérification du challenge Lark
    if "challenge" in body:
        return {
            "statusCode": 200,
            "body": json.dumps({"challenge": body["challenge"]})
        }
    
    event_type = body.get("event", {}).get("type")
    if event_type == "im.message.receive_v1":
        msg_content = json.loads(body["event"]["message"]["content"])
        user_question = msg_content.get("text", "")
        chat_id = body["event"]["message"]["chat_id"]
        
        # Appel à DeepSeek
        headers = {
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
            "Content-Type": "application/json"
        }
        deepseek_response = requests.post(
            "https://api.deepseek.com/v1/chat/completions",
            headers=headers,
            json={
                "model": "deepseek-chat",
                "messages": [{"role": "user", "content": user_question}]
            }
        )
        answer = deepseek_response.json()["choices"][0]["message"]["content"]
        
        # Envoyer la réponse dans Lark
        send_message_to_lark(chat_id, answer)
    
    return {
        "statusCode": 200,
        "body": "ok"
    }
