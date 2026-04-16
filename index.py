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
        data["reply_markup"] = {
            "inline_keyboard": buttons
        }

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
        "🚫 *Access Denied!*\n\n🔒 Join all channels first to use *LEGEND 99 EXTRACTER*.\n\n👇 After joining click *VERIFY JOIN*.",
        buttons
    )

def extract_redirects(url):
    redirects = []
    current_url = url
    session = requests.Session()

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    for _ in range(10):
        try:
            r = session.get(
                current_url,
                allow_redirects=False,
                headers=headers,
                timeout=10
            )

            next_url = None

            # Location header redirect
            if "Location" in r.headers:
                next_url = r.headers["Location"]

            # JavaScript redirect
            if not next_url:
                match = re.search(
                    r'window\.location(?:\.href)?\s*=\s*["\'](.*?)["\']',
                    r.text,
                    re.I
                )
                if match:
                    next_url = match.group(1)

            # Meta refresh redirect
            if not next_url:
                match = re.search(
                    r'http-equiv=["\']?refresh["\']?.*url=(.*?)["\']',
                    r.text,
                    re.I
                )
                if match:
                    next_url = match.group(1)

            if next_url:
                if next_url.startswith("/"):
                    next_url = urljoin(current_url, next_url)

                redirects.append(next_url)
                current_url = next_url
            else:
                break

        except:
            break

    return redirects

@app.route("/", methods=["GET", "POST"])
def webhook():

    if request.method == "GET":
        return "Bot is running"

    update = request.json

    if "callback_query" in update:
        chat_id = update["callback_query"]["message"]["chat"]["id"]
        user_id = update["callback_query"]["from"]["id"]
        data = update["callback_query"]["data"]

        if data == "verify_join":
            if is_joined(user_id):
                send_message(
                    chat_id,
                    "🎉 *Verification Successful!*\n\n✅ Welcome to *LEGEND 99 EXTRACTER*\n\n🔗 Send me any URL to extract redirect links."
                )
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
            "🎉 *WELCOME TO LEGEND 99 EXTRACTER* 🎉\n\n🔗 Send me any URL and I will extract redirect links for you.\n\n⚡ *Ready to extract!*"
        )
        return "ok"

    if not text.startswith("http"):
        send_message(
            chat_id,
            "❌ *Invalid URL!*\n\nPlease send a valid URL like:\n`https://example.com`"
        )
        return "ok"

    send_message(
        chat_id,
        "⏳ *Please wait...*\n\n🔍 Extracting redirect links..."
    )

    redirects = extract_redirects(text)

    if not redirects:
        send_message(
            chat_id,
            "⚠️ *No Redirect Links Found!*"
        )
        return "ok"

    msg = "✅ *Redirect Links Extracted:*\n\n"

    for i, link in enumerate(redirects, 1):
        msg += f"🔹 *Step {i}*\n`{link}`\n\n"

    msg += "🎉 *Done!*"

    send_message(chat_id, msg)

    return "ok"