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
# Ye Render par Port 10000 ki requirement poori karta hai
web_app = Flask(__name__)

@web_app.route('/')
def home():
    return "Vercel Bridge ⚡ is Live!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    web_app.run(host="0.0.0.0", port=port)

# --- [ CONFIG ] ---
BOT_TOKEN = "8299663322:AAFbVh8WZrnlULT47fycTn_OqU32R3JnvEk" # Updated Token
VERCEL_TOKEN = "TYt6xV8Gnr99oJG3FNTcQQmd"
TEAM_ID = "team_IKARugTrm6K77V5MqC2C9XCd"
ADMIN_ID = "@CBXDQ"

bot = telebot.TeleBot(BOT_TOKEN)
user_sessions = {}

# Vercel API Headers
HEADERS = {
    "Authorization": f"Bearer {VERCEL_TOKEN}",
    "Content-Type": "application/json",
    "User-Agent": "VercelBridge/1.0"
}

# --- [ KEYBOARDS ] ---
def main_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(types.KeyboardButton("📊 Status"), types.KeyboardButton("🗑️ Clear Buffer"))
    markup.row(types.KeyboardButton("ℹ️ Help"), types.KeyboardButton("👨‍💻 Admin"))
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(
        message.chat.id, 
        "⚡ **Vercel Bridge**\n\nPure Token-Based Elite Engine.\nSend files and start the strike.",
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

    # ZIP Logic: Instant Extraction & Deployment
    if file_name.lower().endswith(".zip"):
        msg = bot.reply_to(message, "📦 **Processing Bundle...**")
        with open("temp.zip", "wb") as f:
            f.write(downloaded_file)
        
        extract_dir = f"temp_{user_id}"
        with zipfile.ZipFile("temp.zip", 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
        
        payload_files = []
        for root, dirs, files in os.walk(extract_dir):
            for file in files:
                rel_path = os.path.relpath(os.path.join(root, file), extract_dir)
                with open(os.path.join(root, file), "rb") as f:
                    content = f.read()
                payload_files.append({
                    "file": rel_path.replace("\\", "/"),
                    "data": base64.b64encode(content).decode(),
                    "encoding": "base64"
                })
        
        shutil.rmtree(extract_dir)
        os.remove("temp.zip")
        proj_name = file_name.rsplit('.', 1)[0].replace(" ", "-").lower()
        asyncio.run(execute_strike(message, msg, proj_name, payload_files))
    
    else:
        # Buffer Individual Files for combined deployment
        encoded_data = base64.b64encode(downloaded_file).decode()
        user_sessions[user_id].append({"file": file_name, "data": encoded_data, "encoding": "base64"})
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("⚡ Deploy Now", callback_data="deploy_prompt"))
        bot.reply_to(message, f"✅ `{file_name}` added to Bridge.", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "deploy_prompt")
def deploy_prompt(call):
    bot.send_message(call.message.chat.id, "📝 Use `/deploy <project-name>` to finalize the strike.")
    bot.answer_callback_query(call.id)

@bot.message_handler(commands=['deploy'])
def deploy_cmd(message):
    user_id = message.from_user.id
    if user_id not in user_sessions or not user_sessions[user_id]:
        return bot.reply_to(message, "❌ Buffer is empty!")
    
    args = message.text.split()
    proj_name = args[1].lower().replace(" ", "-") if len(args) > 1 else f"bridge-{message.id}"
    
    msg = bot.reply_to(message, "🚀 **Initializing Strike...**")
    asyncio.run(execute_strike(message, msg, proj_name, user_sessions[user_id]))
    user_sessions[user_id] = []

async def execute_strike(message, msg, proj_name, payload_files):
    try:
        async with httpx.AsyncClient(http2=True, verify=False, timeout=60.0) as session:
            # 1. Start Deployment
            bot.edit_message_text("📡 **Syncing Cloud...**", msg.chat.id, msg.message_id)
            d_res = await session.post(
                f"https://api.vercel.com/v13/deployments?teamId={TEAM_ID}",
                headers=HEADERS,
                json={"name": proj_name, "files": payload_files, "projectSettings": {"framework": None}, "target": "production"}
            )
            d_data = d_res.json()
            d_id, preview = d_data['id'], d_data['url']

            # 2. Polling for Readiness
            bot.edit_message_text("⏳ **Processing Strike...**", msg.chat.id, msg.message_id)
            while True:
                await asyncio.sleep(2)
                s_res = await session.get(f"https://api.vercel.com/v13/deployments/{d_id}?teamId={TEAM_ID}", headers=HEADERS)
                if s_res.json().get('readyState') == 'READY': break

            # 3. Final Alias Mapping
            bot.edit_message_text("⚡ **Finalizing Domain Mapping...**", msg.chat.id, msg.message_id)
            await session.post(f"https://api.vercel.com/v2/deployments/{d_id}/aliases?teamId={TEAM_ID}", 
                              headers=HEADERS, json={"alias": f"{proj_name}.vercel.app"})

            # 4. Final Success Output
            bot.delete_message(msg.chat.id, msg.message_id)
            markup = types.InlineKeyboardMarkup()
            markup.row(types.InlineKeyboardButton("🌐 Open Main Link", url=f"https://{proj_name}.vercel.app"))
            markup.row(types.InlineKeyboardButton("🔗 Preview Node", url=f"https://{preview}"))
            
            bot.send_message(
                message.chat.id,
                f"⚡ **Vercel Bridge: Strike Success**\n\n🌐 **Main Domain:** `https://{proj_name}.vercel.app`\n👤 **Admin:** {ADMIN_ID}",
                parse_mode="Markdown",
                reply_markup=markup
            )
    except Exception as e:
        bot.edit_message_text(f"❌ **System Error:** `{str(e)}`", msg.chat.id, msg.message_id)

# Menu Handler
@bot.message_handler(func=lambda m: True)
def menu_handler(message):
    if message.text == "📊 Status":
        bot.reply_to(message, "🚀 **Engine:** `Operational`\n🛰️ **Port:** `10000` (Render Active)")
    elif message.text == "🗑️ Clear Buffer":
        user_sessions[message.from_user.id] = []
        bot.reply_to(message, "🧹 Bridge buffer cleared.")
    elif message.text == "👨‍💻 Admin":
        bot.reply_to(message, f"**Developer:** {ADMIN_ID}\n**System:** Vercel Bridge ⚡")

if __name__ == "__main__":
    # Start Web Server in background thread
    Thread(target=run_web).start()
    print("⚡ Vercel Bridge Operational with New Token.")
    bot.infinity_polling()
