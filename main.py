import json
import requests
import threading
import time
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext
from byte import Encrypt_ID, encrypt_api

# إعداد سجل الأخطاء
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# تحميل التوكنات من ملف JSON
try:
    with open('tokens.json', 'r') as f:
        tokens_data = json.load(f)
    tokens_list = [item['token'] for item in tokens_data]
    logging.info(f"✅ تم تحميل {len(tokens_list)} توكن")
except Exception as e:
    logging.error(f"❌ خطأ في تحميل tokens.json: {e}")
    tokens_list = []

# إعدادات API
URL = "https://clientbp.ggblueshark.com/LikeProfile"
HEADERS = {
    "X-Unity-Version": "2018.4.11f1",
    "ReleaseVersion": "OB48",
    "Content-Type": "application/x-www-form-urlencoded",
    "X-GA": "v1 1",
    "User-Agent": "Dalvik/2.1.0 (Linux; Android 7.1.2)",
    "Host": "clientbp.ggblueshark.com",
    "Connection": "Keep-Alive",
    "Accept-Encoding": "gzip"
}

class RequestThread(threading.Thread):
    def __init__(self, user_id, token, results):
        super().__init__()
        self.user_id = user_id
        self.token = token
        self.results = results

    def run(self):
        try:
            headers = HEADERS.copy()
            headers["Authorization"] = f"Bearer {self.token}"
            encrypted_id = Encrypt_ID(self.user_id)
            data_hex = encrypt_api(f"08{encrypted_id}1007")
            data_bytes = bytes.fromhex(data_hex)
            response = requests.post(URL, headers=headers, data=data_bytes, verify=False, timeout=10)
            self.results.append({
                "status": response.status_code,
                "token": self.token,
                "success": response.status_code == 200,
                "response": response.text[:100] if response.text else ""
            })
        except Exception as e:
            self.results.append({"status": 0, "token": self.token, "success": False, "error": str(e)})

async def send_requests(user_id, update):
    if not tokens_list:
        await update.message.reply_text("❌ لا توجد توكنات متاحة")
        return

    total = len(tokens_list)
    await update.message.reply_text(f"🚀 بدء إرسال {total} طلب لـ {user_id}...")
    results, threads = [], []
    chunk_size = 10
    
    for i in range(0, total, chunk_size):
        chunk = tokens_list[i:i + chunk_size]
        for token in chunk:
            t = RequestThread(user_id, token, results)
            threads.append(t)
            t.start()
            time.sleep(0.1)
        for t in threads[i:i + chunk_size]:
            t.join()
        await update.message.reply_text(f"⏳ تم إرسال {min(i+chunk_size, total)}/{total}")
    
    success = sum(1 for r in results if r['success'])
    failed = total - success
    report = f"📊 النتائج النهائية:\n✅ ناجحة: {success}\n❌ فاشلة: {failed}\n🔗 User ID: {user_id}"
    await update.message.reply_text(report)

async def like_command(update: Update, context: CallbackContext):
    if not context.args:
        await update.message.reply_text("⚡ الاستخدام: /like <user_id>")
        return
    user_id = context.args[0]
    await send_requests(user_id, update)

def run_bot():
    try:
        BOT_TOKEN = "7602367113:AAEd0N-sYTNSULhC5_GE2nq-kRKYv8YgP7s"
        app = Application.builder().token(BOT_TOKEN).read_timeout(30).write_timeout(30).build()
        app.add_handler(CommandHandler("like", like_command))
        logging.info("🤖 البوت يعمل الآن...")
        app.run_polling(drop_pending_updates=True, timeout=20, allowed_updates=Update.ALL_TYPES)
    except Exception as e:
        logging.error(f"🔥 خطأ رئيسي: {e}")

if __name__ == '__main__':
    run_bot()