import os
from dotenv import load_dotenv
from pymongo import MongoClient


load_dotenv()
MONGO_URL = os.getenv("MONGODB_CONNECTION")
client = MongoClient(MONGO_URL)

def read_data():
    data = client['Autosub_PTIT']['accounts'].find()
    for item in data:
        print(item)
    return

def isvalid_account(account):
    return client['Autosub_PTIT']['accounts'].find_one({"account": account}) != None

