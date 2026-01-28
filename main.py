import os
import asyncio
import base64
import httpx
import shutil
import zipfile
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

# --- [ CREDITS & CONFIG ] ---
API_ID = "25139739"
API_HASH = "81427282b0f496156e9c0c3258838334"
BOT_TOKEN = "7864871444:AAFe3oR1p0DqS1H9y2fS0W_7V107U2_Nstk"

VERCEL_TOKEN = "TYt6xV8Gnr99oJG3FNTcQQmd"
TEAM_ID = "team_IKARugTrm6K77V5MqC2C9XCd"
ADMIN_ID = "@CBXDQ"

HEADERS = {
    "Authorization": f"Bearer {VERCEL_TOKEN}",
    "User-Agent": "Mozilla/5.0 (Linux; Android 12; LAVA Blaze)",
    "Content-Type": "application/json"
}

app = Client("VercelBridge", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Buffer and session management
user_sessions = {}

# --- [ KEYBOARDS ] ---
# Bottom Keyboard (Main Menu)
MAIN_KEYBOARD = ReplyKeyboardMarkup(
    [
        [KeyboardButton("📊 Status"), KeyboardButton("🗑️ Clear Buffer")],
        [KeyboardButton("ℹ️ Help"), KeyboardButton("👨‍💻 Admin")]
    ],
    resize_keyboard=True
)

@app.on_message(filters.command("start"))
async def start_cmd(client, message):
    await message.reply_text(
        "⚡ **Vercel Bridge**\n\n"
        "Welcome to the Elite Cloud Deployment Engine.\n\n"
        "• Send a **ZIP** for full project strike.\n"
        "• Send individual files then click **Deploy**.",
        reply_markup=MAIN_KEYBOARD
    )

# Handle Keyboard Buttons
@app.on_message(filters.text)
async def handle_text(client, message):
    user_id = message.from_user.id
    txt = message.text

    if txt == "📊 Status":
        count = len(user_sessions.get(user_id, []))
        await message.reply_text(f"🚀 **Engine Status:** `Operational`\n📦 **Files in Buffer:** `{count}`")
    
    elif txt == "🗑️ Clear Buffer":
        user_sessions[user_id] = []
        await message.reply_text("🧹 **Bridge buffer cleared.**")
        
    elif txt == "ℹ️ Help":
        await message.reply_text("1. Send files (HTML/CSS/JS).\n2. Use `/deploy <name>` to finish.\n3. Or send a ZIP for instant map.")
        
    elif txt == "👨‍💻 Admin":
        await message.reply_text(f"**Developer:** {ADMIN_ID}\n**Powered by:** Vercel Bridge Engine")

@app.on_message(filters.document)
async def handle_docs(client, message):
    user_id = message.from_user.id
    if user_id not in user_sessions:
        user_sessions[user_id] = []

    # ZIP Logic
    if message.document.file_name.lower().endswith(".zip"):
        msg = await message.reply_text("📦 **Extracting Bundle...**")
        path = await message.download()
        
        extract_dir = f"temp_{user_id}"
        with zipfile.ZipFile(path, 'r') as zip_ref:
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
        os.remove(path)
        proj_name = message.document.file_name.rsplit('.', 1)[0].replace(" ", "-")
        await execute_deployment(message, msg, proj_name, payload_files)
    
    else:
        # File Buffering
        path = await message.download()
        with open(path, "rb") as f:
            user_sessions[user_id].append({
                "file": message.document.file_name,
                "data": base64.b64encode(f.read()).decode(),
                "encoding": "base64"
            })
        os.remove(path)
        
        # Inline button to trigger deploy after file upload
        btn = InlineKeyboardMarkup([[InlineKeyboardButton("⚡ Deploy Now", callback_data="trigger_deploy")]])
        await message.reply_text(f"✅ `{message.document.file_name}` added.", reply_markup=btn)

@app.on_callback_query(filters.regex("trigger_deploy"))
async def cb_deploy(client, callback_query):
    await callback_query.message.reply_text("📝 Send `/deploy <project-name>` to start the strike!")
    await callback_query.answer()

@app.on_message(filters.command("deploy"))
async def deploy_trigger(client, message):
    user_id = message.from_user.id
    if user_id not in user_sessions or not user_sessions[user_id]:
        return await message.reply_text("❌ Buffer is empty.")
    
    if len(message.command) < 2:
        return await message.reply_text("❌ Usage: `/deploy <name>`")

    proj_name = message.command[1].lower().replace(" ", "-")
    msg = await message.reply_text("🚀 **Initializing Deployment...**")
    
    files = user_sessions[user_id]
    await execute_deployment(message, msg, proj_name, files)
    user_sessions[user_id] = [] 

async def execute_deployment(message, msg, proj_name, payload_files):
    try:
        async with httpx.AsyncClient(http2=True, verify=False, timeout=60.0) as session:
            await msg.edit("📡 **Syncing Payload...**")
            d_res = await session.post(
                f"https://api.vercel.com/v13/deployments?teamId={TEAM_ID}",
                headers=HEADERS,
                json={
                    "name": proj_name, 
                    "files": payload_files, 
                    "projectSettings": {"framework": None},
                    "target": "production"
                }
            )
            
            d_data = d_res.json()
            if "id" not in d_data:
                await msg.edit(f"❌ **Error:** `{d_data.get('error', {}).get('message', 'Unknown')}`")
                return

            d_id = d_data['id']
            preview = d_data['url']

            await msg.edit("⏳ **Processing Files...**")
            while True:
                await asyncio.sleep(2)
                s_res = await session.get(f"https://api.vercel.com/v13/deployments/{d_id}?teamId={TEAM_ID}", headers=HEADERS)
                if s_res.json().get('readyState') == 'READY':
                    break

            await msg.edit("⚡ **Finalizing Domain Mapping...**")
            await session.post(
                f"https://api.vercel.com/v2/deployments/{d_id}/aliases?teamId={TEAM_ID}",
                headers=HEADERS,
                json={"alias": f"{proj_name}.vercel.app"}
            )

            await msg.delete()
            final_text = (
                "⚡ **Vercel Bridge: Strike Success**\n\n"
                f"🌐 **Main Link:** `https://{proj_name}.vercel.app`\n"
                f"🔗 **Preview Node:** `https://{preview}`\n\n"
                f"**Owner:** {ADMIN_ID}"
            )
            
            # Action Buttons
            res_btns = InlineKeyboardMarkup([
                [InlineKeyboardButton("🌐 Open Main Link", url=f"https://{proj_name}.vercel.app")],
                [InlineKeyboardButton("🔗 Preview Node", url=f"https://{preview}")]
            ])
            await message.reply_text(final_text, reply_markup=res_btns)

    except Exception as e:
        await msg.edit(f"❌ **System Error:** `{str(e)}`")

print("⚡ Vercel Bridge is Operational with UI.")
app.run()
