import os
import telebot
import base64
import httpx
import asyncio
import zipfile
import shutil
from flask import Flask
from threading import Thread
from telebot import types

# --- [ RENDER WEB SERVER FIX ] ---
web_app = Flask(__name__)

@web_app.route('/')
def home():
    return "Vercel Bridge ⚡ is Live!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    web_app.run(host="0.0.0.0", port=port)

# --- [ CONFIG ] ---
BOT_TOKEN = "8299663322:AAFbVh8WZrnlULT47fycTn_OqU32R3JnvEk"
VERCEL_TOKEN = "TYt6xV8Gnr99oJG3FNTcQQmd"
TEAM_ID = "team_IKARugTrm6K77V5MqC2C9XCd"
ADMIN_ID = "@CBXDQ"

bot = telebot.TeleBot(BOT_TOKEN)
user_sessions = {}

HEADERS = {
    "Authorization": f"Bearer {VERCEL_TOKEN}",
    "Content-Type": "application/json",
    "User-Agent": "VercelBridge/1.0"
}

def main_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(types.KeyboardButton("📊 Status"), types.KeyboardButton("🗑️ Clear Buffer"))
    markup.row(types.KeyboardButton("ℹ️ Help"), types.KeyboardButton("👨‍💻 Admin"))
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(
        message.chat.id, 
        "⚡ **Vercel Bridge**\n\nSystem is now equipped with **Domain Scouting**.\nSend files and use `/deploy <name>`.",
        parse_mode="Markdown",
        reply_markup=main_keyboard()
    )

@bot.message_handler(content_types=['document'])
def handle_docs(message):
    user_id = message.from_user.id
    if user_id not in user_sessions:
        user_sessions[user_id] = []

    file_info = bot.get_file(message.document.file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    file_name = message.document.file_name

    if file_name.lower().endswith(".zip"):
        msg = bot.reply_to(message, "📝 **Enter desired project name for this ZIP:**")
        bot.register_next_step_handler(msg, process_zip_deployment, downloaded_file, file_name)
    else:
        encoded_data = base64.b64encode(downloaded_file).decode()
        user_sessions[user_id].append({"file": file_name, "data": encoded_data, "encoding": "base64"})
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("⚡ Deploy Now", callback_data="deploy_prompt"))
        bot.reply_to(message, f"✅ `{file_name}` added to Bridge.", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "deploy_prompt")
def deploy_prompt(call):
    bot.send_message(call.message.chat.id, "📝 Use `/deploy <project-name>` to start scouting.")
    bot.answer_callback_query(call.id)

@bot.message_handler(commands=['deploy'])
def deploy_cmd(message):
    user_id = message.from_user.id
    if user_id not in user_sessions or not user_sessions[user_id]:
        return bot.reply_to(message, "❌ Buffer is empty!")
    
    args = message.text.split()
    if len(args) < 2:
        return bot.reply_to(message, "❌ Please provide a name: `/deploy my-cool-site`")
    
    proj_name = args[1].lower().replace(" ", "-")
    msg = bot.reply_to(message, f"🔍 **Scouting domain:** `{proj_name}.vercel.app`...")
    
    asyncio.run(check_and_strike(message, msg, proj_name, user_sessions[user_id]))
    user_sessions[user_id] = []

async def check_and_strike(message, msg, proj_name, payload_files):
    try:
        async with httpx.AsyncClient(http2=True, verify=False, timeout=60.0) as session:
            # --- PHASE 0: DOMAIN SCOUTING ---
            check_url = f"https://api.vercel.com/v4/domains/status?name={proj_name}.vercel.app&teamId={TEAM_ID}"
            c_res = await session.get(check_url, headers=HEADERS)
            
            # Agar domain already taken hai
            if c_res.status_code == 200 and not c_res.json().get("available", True):
                bot.edit_message_text(f"❌ **Domain Taken:** `{proj_name}.vercel.app` is already booked.\nTry another name with `/deploy <new-name>`", msg.chat.id, msg.message_id)
                user_sessions[message.from_user.id] = payload_files # Restore buffer
                return

            # --- PHASE 1: DEPLOYMENT ---
            bot.edit_message_text("📡 **Domain Available! Syncing Cloud...**", msg.chat.id, msg.message_id)
            d_res = await session.post(
                f"https://api.vercel.com/v13/deployments?teamId={TEAM_ID}",
                headers=HEADERS,
                json={"name": proj_name, "files": payload_files, "projectSettings": {"framework": None}, "target": "production"}
            )
            d_data = d_res.json()
            d_id, preview = d_data['id'], d_data['url']

            # --- PHASE 2: POLLING ---
            bot.edit_message_text("⏳ **Processing Strike...**", msg.chat.id, msg.message_id)
            while True:
                await asyncio.sleep(2)
                s_res = await session.get(f"https://api.vercel.com/v13/deployments/{d_id}?teamId={TEAM_ID}", headers=HEADERS)
                if s_res.json().get('readyState') == 'READY': break

            # --- PHASE 3: ALIASING ---
            bot.edit_message_text("⚡ **Finalizing Domain Mapping...**", msg.chat.id, msg.message_id)
            await session.post(f"https://api.vercel.com/v2/deployments/{d_id}/aliases?teamId={TEAM_ID}", 
                              headers=HEADERS, json={"alias": f"{proj_name}.vercel.app"})

            bot.delete_message(msg.chat.id, msg.message_id)
            markup = types.InlineKeyboardMarkup()
            markup.row(types.InlineKeyboardButton("🌐 Open Main Link", url=f"https://{proj_name}.vercel.app"))
            bot.send_message(message.chat.id, f"⚡ **Strike Success**\n\n🌐 **Main:** `https://{proj_name}.vercel.app`", parse_mode="Markdown", reply_markup=markup)

    except Exception as e:
        bot.edit_message_text(f"❌ **System Error:** `{str(e)}`", msg.chat.id, msg.message_id)

def process_zip_deployment(message, downloaded_file, file_name):
    proj_name = message.text.lower().replace(" ", "-")
    msg = bot.reply_to(message, f"🔍 **Scouting domain for ZIP:** `{proj_name}.vercel.app`...")
    
    # Extraction Logic
    with open("temp.zip", "wb") as f: f.write(downloaded_file)
    extract_dir = f"temp_zip_{message.from_user.id}"
    with zipfile.ZipFile("temp.zip", 'r') as zip_ref: zip_ref.extractall(extract_dir)
    
    payload_files = []
    for root, _, files in os.walk(extract_dir):
        for file in files:
            rel_path = os.path.relpath(os.path.join(root, file), extract_dir)
            with open(os.path.join(root, file), "rb") as f:
                payload_files.append({"file": rel_path.replace("\\", "/"), "data": base64.b64encode(f.read()).decode(), "encoding": "base64"})
    
    shutil.rmtree(extract_dir)
    os.remove("temp.zip")
    asyncio.run(check_and_strike(message, msg, proj_name, payload_files))

if __name__ == "__main__":
    Thread(target=run_web).start()
    bot.infinity_polling()
