from flask import Flask, request, jsonify
import json
import os
import requests
import traceback

app = Flask(__name__)

DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY")
LARK_APP_ID = os.environ.get("LARK_APP_ID")
LARK_APP_SECRET = os.environ.get("LARK_APP_SECRET")


def get_tenant_access_token():
    resp = requests.post(
        "https://open.larksuite.com/open-apis/auth/v3/tenant_access_token/internal",
        json={"app_id": LARK_APP_ID, "app_secret": LARK_APP_SECRET},
    )
    return resp.json()["tenant_access_token"]


def send_message_to_lark(chat_id, text):
    token = get_tenant_access_token()
    payload = {
        "receive_id": chat_id,
        "msg_type": "text",
        "content": json.dumps({"text": text}),
    }
    requests.post(
        "https://open.larksuite.com/open-apis/im/v1/messages?receive_id_type=chat_id",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        json=payload,
    )


@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.json

        # Challenge de vérification Lark
        if "challenge" in data:
            return jsonify({"challenge": data["challenge"]})

        event = data.get("event", {})
        if event.get("type") == "im.message.receive_v1":
            msg_content = json.loads(event["message"]["content"])
            user_question = msg_content.get("text", "")
            chat_id = event["message"]["chat_id"]

            headers = {
                "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                "Content-Type": "application/json",
            }
            deepseek_resp = requests.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers=headers,
                json={
                    "model": "deepseek-chat",
                    "messages": [{"role": "user", "content": user_question}],
                },
            )
            answer = deepseek_resp.json()["choices"][0]["message"]["content"]
            send_message_to_lark(chat_id, answer)

        return jsonify({"status": "ok"})

    except Exception as e:
        # En cas d'erreur, on renvoie un JSON avec le message
        return jsonify({"error": str(e), "traceback": traceback.format_exc()}), 500


# Route de test GET (facultative)
@app.route("/webhook", methods=["GET"])
def webhook_get():
    return jsonify({"message": "Webhook is running. Send a POST request."})
