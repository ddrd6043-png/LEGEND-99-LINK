from flask import Flask, request
import requests
import re
from urllib.parse import urljoin

app = Flask(__name__)

BOT_TOKEN = "8535220223:AAEMFAtTPYaOC-4rYzSFCZoj-nIcbVEGb_A"
API = f"https://api.telegram.org/bot{BOT_TOKEN}/"

channels = [
    "@legend99loots",
    "@legend99chats",
    "-1003866614306"
]

def send_message(chat_id, text, buttons=None):
    data = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown"
    }

    if buttons:
        data["reply_markup"] = {"inline_keyboard": buttons}

    requests.post(API + "sendMessage", json=data)

def is_joined(user_id):
    for channel in channels:
        try:
            r = requests.get(API + "getChatMember", params={
                "chat_id": channel,
                "user_id": user_id
            }).json()

            status = r.get("result", {}).get("status", "")
            if status not in ["member", "administrator", "creator"]:
                return False
        except:
            return False
    return True

def send_join_message(chat_id):
    buttons = [
        [
            {"text":"📢 JOIN LOOTS", "url":"https://t.me/legend99loots"},
            {"text":"💬 JOIN CHATS", "url":"https://t.me/legend99chats"}
        ],
        [
            {"text":"🚀 JOIN VIP", "url":"https://t.me/+oAZlJUvq2C9iMzE1"}
        ],
        [
            {"text":"✅ VERIFY JOIN", "callback_data":"verify_join"}
        ]
    ]

    send_message(
        chat_id,
        "🚫 *Access Denied!*\n\n🔒 Join all channels first.\n\n👇 Then click *VERIFY JOIN*.",
        buttons
    )

def extract_redirects(url):
    redirects = []
    current_url = url
    session = requests.Session()

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    try:
        for _ in range(10):
            r = session.get(
                current_url,
                allow_redirects=False,
                headers=headers,
                timeout=10
            )

            next_url = None

            # Header redirect
            if "Location" in r.headers:
                next_url = r.headers["Location"]

            # JS redirect
            if not next_url:
                patterns = [
                    r'window\.location(?:\.href)?\s*=\s*["\'](.*?)["\']',
                    r'location\.replace\(["\'](.*?)["\']\)',
                    r'window\.open\(["\'](.*?)["\']'
                ]

                for pattern in patterns:
                    match = re.search(pattern, r.text, re.I)
                    if match:
                        next_url = match.group(1)
                        break

            if next_url:
                next_url = urljoin(current_url, next_url)

                if next_url in redirects:
                    break

                redirects.append(next_url)
                current_url = next_url
            else:
                break

        # If no redirects found, get final URL
        if not redirects:
            r = session.get(url, allow_redirects=True, headers=headers, timeout=10)
            redirects.append(r.url)

    except:
        return []

    return redirects

@app.route("/", methods=["GET", "POST"])
def webhook():

    if request.method == "GET":
        return "Bot is running"

    update = request.json

    # Callback query
    if "callback_query" in update:
        chat_id = update["callback_query"]["message"]["chat"]["id"]
        user_id = update["callback_query"]["from"]["id"]
        data = update["callback_query"]["data"]

        if data == "verify_join":
            if is_joined(user_id):
                send_message(chat_id, "✅ *Verification Successful!*\n\nNow send a URL.")
            else:
                send_join_message(chat_id)

        return "ok"

    if "message" not in update:
        return "ok"

    chat_id = update["message"]["chat"]["id"]
    user_id = update["message"]["from"]["id"]
    text = update["message"].get("text", "").strip()

    if not is_joined(user_id):
        send_join_message(chat_id)
        return "ok"

    if text == "/start":
        send_message(
            chat_id,
            "🎉 *WELCOME TO LEGEND 99 EXTRACTER*\n\n🔗 Send URL to extract redirects."
        )
        return "ok"

    if not text.startswith("http"):
        send_message(
            chat_id,
            "❌ *Invalid URL!*\n\nSend valid URL like:\n`https://example.com`"
        )
        return "ok"

    send_message(chat_id, "⏳ *Extracting redirect links...*")

    redirects = extract_redirects(text)

    if not redirects:
        send_message(chat_id, "⚠️ *No Redirect Links Found!*")
        return "ok"

    msg = "✅ *Redirect Links Extracted:*\n\n"

    for i, link in enumerate(redirects, 1):
        msg += f"🔹 *Step {i}:*\n`{link}`\n\n"

    msg += "🎉 *Done!*"

    send_message(chat_id, msg)

    return "ok"