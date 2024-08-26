import json
import redis
import asyncio
from pymongo import MongoClient
import os
import requests
from dotenv import load_dotenv

# Load env
load_dotenv()

DOMAIN = os.getenv("DOMAIN")
MONGO_URL = os.getenv("MONGODB_CONNECTION")
client = MongoClient(MONGO_URL)
redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
accounts_collection = client['Autosub_PTIT']['accounts']

def is_account_valid(account, password):
    url = f"{DOMAIN}/check-account?username={account}&password={password}"
    response = requests.get(url)
    return response.status_code == 200

async def handle_redis_messages(redis_client):
    pubsub = redis_client.pubsub()
    pubsub.subscribe('addaccount', 'delaccount')

    while True:
        message = pubsub.get_message()

        if message and message['type'] == 'message':
            channel = message['channel']
            data = message['data']

            if channel == 'addaccount':
                await handle_add_account(data)
            elif channel == 'delaccount':
                await handle_delete_account(data)

        await asyncio.sleep(0.1)

async def handle_add_account(data):
    try:
        account_info = json.loads(data)
        account = account_info['account']
        password = account_info['password']

        if is_account_valid(account, password):
            print(f"Đăng nhập thành công cho tài khoản: {account}")
            if not accounts_collection.find_one({"account": account}):
                accounts_collection.insert_one({"account": account, "password": password})
                print(f"Tài khoản {account} đã được thêm vào MongoDB")
    except json.JSONDecodeError:
        print("Không thể giải mã tin nhắn JSON")

async def handle_delete_account(data):
    account = data
    if accounts_collection.find_one({"account": account}):
        accounts_collection.delete_one({"account": account})
        print(f"Tài khoản {account} đã được xóa khỏi MongoDB")


def main():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(handle_redis_messages(redis_client))

if __name__ == "__main__":
    main()
