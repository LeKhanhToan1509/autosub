import json, os
import redis
import database
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, CommandHandler, filters
import requests
from dotenv import load_dotenv

load_dotenv()

DOMAIN = os.getenv("DOMAIN")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE, r: redis.Redis):
    text_received = update.message.text.strip()
    chat_id = update.message.chat_id
    parts = text_received.split(' ')
    first = parts[0]

    if (len(parts) > 3 or first not in ['addacc', 'delacc', 'check', 'help']):
        await context.bot.send_message(chat_id=chat_id, text="Đây là tool tự động nộp bài tại CodePTIT cho các bạn !\nCác lệnh:\n- addacc [tài khoản] [mật khẩu]: Thêm tài khoản vào hệ thống.\n- delacc [tài khoản]: Xóa tài khoản khỏi hệ thống.\n- check [tài khoản] [mật khẩu]: Kiểm tra số câu hỏi chưa làm của tài khoản.\n- help: Hiển thị danh sách các lệnh.")
        return
    else:
        command = text_received.split()[0]
        if command == "addacc":
            account = text_received.split()[1]
            if(len(text_received.split()) != 3):
                await context.bot.send_message(chat_id=chat_id, text="Cú pháp đúng là : addacc [tài khoản] [mật khẩu].")
            else:
                password = text_received.split()[2]
            if account:
                if not database.isvalid_account(account):
                    information = json.dumps({"account": account, "password": password})
                    r.publish("addaccount", information)
                    await context.bot.send_message(chat_id=chat_id, text=f"Đang xác minh tài khoản của bạn ...")
                    url = f"{DOMAIN}/check-account?username={account}&password={password}"
                    response = requests.get(url)
                    if response.status_code == 200:
                        await context.bot.send_message(chat_id=chat_id, text="Tài khoản của bạn chính xác ! Đã được thêm vào hệ thống.")
                    else:
                        await context.bot.send_message(chat_id=chat_id, text="Tài khoản không hợp lệ.")
                else:
                    await context.bot.send_message(chat_id=chat_id, text="Tài khoản đã tồn tại trong hệ thống.")
            else:
                await context.bot.send_message(chat_id=chat_id, text="Vui lòng nhập đủ tài khoản và mật khẩu.")
        
        elif command == "delacc":
            if(len(text_received.split()) != 2):
                await context.bot.send_message(chat_id=chat_id, text="Cú pháp đúng là : delacc [tài khoản].")
            else:
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
            if(len(text_received.split()) != 3):
                await context.bot.send_message(chat_id=chat_id, text="Cú pháp đúng là : check [tài khoản] [mật khẩu].")
            else:
                password = text_received.split()[2]
            if account:
                url = f"{DOMAIN}/not-done?username={account}&password={password}"
                response = requests.get(url)
                if response.status_code == 200:
                    less = response.json().get('not_done', 0)
                    await context.bot.send_message(chat_id=chat_id, text=f"Tài khoản của bạn còn {less} câu hỏi chưa làm.")
                else:
                    await context.bot.send_message(chat_id=chat_id, text="Tài khoản của bạn không hợp lệ.")
            else:
                await context.bot.send_message(chat_id=chat_id, text="Vui lòng nhập tài khoản.")
        
        elif command == "help":
            await context.bot.send_message(chat_id=chat_id, text="Đây là tool tự động nộp bài tại CodePTIT cho các bạn !\nCác lệnh:\n- addacc [tài khoản] [mật khẩu]: Thêm tài khoản vào hệ thống.\n- delacc [tài khoản]: Xóa tài khoản khỏi hệ thống.\n- check [tài khoản] [mật khẩu]: Kiểm tra số câu hỏi chưa làm của tài khoản.\n- help: Hiển thị danh sách các lệnh.")

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE, r: redis.Redis):
    await handle_message(update, context, r)

def main():
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    r = redis.Redis(host='localhost', port=6379, decode_responses=True)
    
    app.add_handler(CommandHandler("start", lambda update, context: start_command(update, context, r)))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, lambda update, context: handle_message(update, context, r)))

    app.run_polling()

if __name__ == "__main__":
    main()
