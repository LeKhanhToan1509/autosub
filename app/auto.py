import requests
from dotenv import load_dotenv
import os
from pymongo import MongoClient
import logging
import schedule
import time

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MONGODB_URL = os.getenv("MONGODB_URL")
DOMAIN = os.getenv("DOMAIN")

db = MongoClient(MONGODB_URL).get_database("Autosub_PTIT")

def auto_sub_code():
    try:
        accounts = db['accounts'].find()
    except Exception as e:
        logger.error(f"Lỗi khi kết nối tới MongoDB: {e}")
        return
    
    for acc in accounts:
        username = acc.get('account')
        password = acc.get('password')
        try:
            response = requests.post(f"{DOMAIN}/submit-files?username={username}&password={password}")
            response.raise_for_status() 
            logger.info(f"Submitted for {username}: {response.status_code}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Lỗi khi gửi yêu cầu cho {username}: {e}")

schedule.every().day.at("00:00").do(auto_sub_code)

if __name__ == "__main__":
    while True:
        schedule.run_pending()
        time.sleep(1)
