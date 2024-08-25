import json
import redis
import asyncio
from pymongo import MongoClient
import os
import requests
from dotenv import load_dotenv
load_dotenv()

DOMAIN = os.getenv("DOMAIN")
MONGO_URL = os.getenv("MONGODB_CONNECTION")
client = MongoClient(MONGO_URL)
r = redis.Redis(host='localhost', port=6379, decode_responses=True)



async def listen_to_redis(r):
    add = r.pubsub()
    rm = r.pubsub()
    add.subscribe('addaccount')
    rm.subscribe('delaccount')
    acc = client['Autosub_PTIT']['accounts']
    while True:
        add_data = add.get_message()
        rm_data = rm.get_message()

        if add_data:
            message = add_data['data']
            if message != 1:
                info = json.loads(message)
                account = info['account']
                password = info['password']
                url = f"{DOMAIN}/check-account?username={account}&password={password}"
                response = requests.request("GET", url)
                if response.status_code == 200:
                    print("Login success")
                    if(acc.find_one({"account": account}) == None):
                        acc.insert_one({"account": account, "password": password})
        if rm_data:
            message = rm_data['data']
            if message != 1:  
                account = message
                if(acc.find_one({"account": account}) != None):
                    acc.delete_one({"account": account})
        await asyncio.sleep(0.1) 

def main():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(listen_to_redis(r))

if __name__ == "__main__":
    main()
