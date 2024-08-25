import json, os
import redis
import database
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters
import requests
from dotenv import load_dotenv
load_dotenv()

DOMAIN = os.getenv("DOMAIN")
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE, r: redis.Redis):
    text_received = update.message.text.strip()
    chat_id = update.message.chat_id
    parts = text_received.split()

    if (len(parts) > 3 ):
        await context.bot.send_message(chat_id=chat_id, text="Sai cú pháp. Vui lòng nhập đúng cú pháp lệnh.")
        await context.bot.send_message(chat_id=chat_id, text="Gõ 'help' để xem danh sách các lệnh.")
    else:
        command = text_received.split()[0]
        if command == "addacc":
            account = text_received.split()[1]
            password = text_received.split()[2]
            if account:
                if database.isvalid_account(account) == False:
                    information = json.dumps({"account": account, "password": password})
                    r.publish("addaccount", information)
                    await context.bot.send_message(chat_id=chat_id, text=f"Đang thêm tài khoản {account} vào hệ thống...")
                    url = f"{DOMAIN}/check-account?username={account}&password={password}"
                    response = requests.request("GET", url)
                    if response.status_code == 200:
                        await context.bot.send_message(chat_id=chat_id, text="Tài khoản của bạn chính xác ! Đang chờ xác nhận thêm vào hệ thống.")
                    else:
                        await context.bot.send_message(chat_id=chat_id, text="Tài khoản không hợp lệ.")
                else:
                    await context.bot.send_message(chat_id=chat_id, text="Tài khoản đã tồn tại trong hệ thống.")
            else:
                await context.bot.send_message(chat_id=chat_id, text="Vui lòng nhập đủ tài khoản và mật khẩu.")
        
        elif command == "delacc":
            account = text_received.split()[1]
            if account:
                if database.isvalid_account(account):
                    r.publish("delaccount", account)
                    await context.bot.send_message(chat_id=chat_id, text=f"Tài khoản của bạn đã được xóa khỏi hệ thống.")
                else:
                    await context.bot.send_message(chat_id=chat_id, text=f"Tài khoản của bạn không tồn tại trong hệ thống.")
            else:
                await context.bot.send_message(chat_id=chat_id, text="Vui lòng nhập tài khoản.")
        
        elif command == "check":
            account = text_received.split()[1]
            password = text_received.split()[2]
            if account:
                url = f"{DOMAIN}/not-done?username={account}&password={password}"
                response = requests.request("GET", url)
                if response.status_code == 200:
                    less = response.json().get('not_done', 0)
                    await context.bot.send_message(chat_id=chat_id, text=f"Tài khoản của bạn còn {less} câu hỏi chưa làm.")
                else:
                    await context.bot.send_message(chat_id=chat_id, text="Tài khoản của bạn không hợp lệ.")
            else:
                await context.bot.send_message(chat_id=chat_id, text="Vui lòng nhập tài khoản.")
        elif command == "help":
            await context.bot.send_message(chat_id=chat_id, text="Các lệnh:\n- addacc [tài khoản] [mật khẩu]: Thêm tài khoản vào hệ thống.\n- delacc [tài khoản]: Xóa tài khoản khỏi hệ thống.\n- check [tài khoản] [mật khẩu]: Kiểm tra số câu hỏi chưa làm của tài khoản.\n- help: Hiển thị danh sách các lệnh.")

def main():
    telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
    app = ApplicationBuilder().token(telegram_token).build()
    r = redis.Redis(host='localhost', port=6379, decode_responses=True)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, lambda update, context: handle_message(update, context, r)))

    app.run_polling()

if __name__ == "__main__":
    main()
