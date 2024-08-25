import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, File, UploadFile, Form
from typing import List, Tuple
from pydantic import BaseModel
import requests
from pymongo import MongoClient
from bson.objectid import ObjectId
import time 
import os

load_dotenv()
DOMAIN = os.getenv("DOMAIN")

app = FastAPI()

class FileData(BaseModel):
    file_path: str
    question_code: str
    compiler_id: str

def check_account(username: str, password: str) -> bool:
    login_url = 'https://code.ptit.edu.vn/login'

    session = requests.Session()

    response = session.get(login_url)

    soup = BeautifulSoup(response.text, 'html.parser')
    csrf_token = soup.find('input', {'name': '_token'})['value']

    login_data = {
        '_token': csrf_token,
        'username': username,
        'password': password
    }

    login_response = session.post(login_url, data=login_data)
    
    return login_response.status_code == 200 and 'student/question' in login_response.url

def login(username: str, password: str) -> Tuple[str, str]:
    login_url = 'https://code.ptit.edu.vn/login'

    session = requests.Session()
    response = session.get(login_url)

    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="Failed to load login page")

    soup = BeautifulSoup(response.text, 'html.parser')
    csrf_token = soup.find('input', {'name': '_token'})['value']

    login_data = {
        '_token': csrf_token,
        'username': username,
        'password': password
    }

    login_response = session.post(login_url, data=login_data)
    
    if login_response.status_code != 200 or 'student/question' not in login_response.url:
        raise HTTPException(status_code=401, detail="Login failed")

    cookies = login_response.cookies.get_dict()
    xsrf_token = cookies.get('XSRF-TOKEN')
    ptit_code_session = cookies.get('ptit_code_session')

    if not xsrf_token or not ptit_code_session:
        raise HTTPException(status_code=401, detail="Failed to retrieve session tokens")

    return xsrf_token, ptit_code_session


def fetch_data(xsrf_token: str, ptit_code_session: str, page: int = None) -> str:
    URL = "https://code.ptit.edu.vn/student/question"
    headers = {
        'Cookie': f'XSRF-TOKEN={xsrf_token}; ptit_code_session={ptit_code_session}'
    }
    if page:
        response = requests.get(URL + f'?page={page}', headers=headers)
    else:
        response = requests.get(URL, headers=headers)
    return response.text

def get_len_page(xsrf_token: str, ptit_code_session: str) -> int:
    page_content = fetch_data(xsrf_token, ptit_code_session)
    soup = BeautifulSoup(page_content, 'html.parser')
    
    pagination = soup.find('ul', {'class': 'pagination'})
    if pagination:
        len_page = len(pagination.find_all('li')) - 2
        return max(1, len_page)
    else:
        return 1

def get_len_not_done_question(xsrf_token: str, ptit_code_session: str) -> int:
    len_page = get_len_page(xsrf_token, ptit_code_session)
    cnt = 0

    for i in range(1, len_page + 1):
        page_content = fetch_data(xsrf_token, ptit_code_session, page=i)
        soup = BeautifulSoup(page_content, 'html.parser')
        arr = soup.find('tbody').find_all('tr')
        for tr in arr:
            if tr.get('class') != ['bg--10th']:
                cnt += 1
    return cnt

def get_files_not_done(xsrf_token: str, ptit_code_session: str, limit: int = 20) -> List[str]:
    len_page = get_len_page(xsrf_token, ptit_code_session)
    arr = []
    while limit > 0:
        for i in range(1, len_page + 1):
            page_content = fetch_data(xsrf_token, ptit_code_session, page=i)
            soup = BeautifulSoup(page_content, 'html.parser')
            rows = soup.find('tbody').find_all('tr')
            for tr in rows:
                if tr.get('class') != ['bg--10th']:
                    alias = tr.find_all('td')[2].find('a').text.strip()
                    arr.append(alias)
                    limit -= 1
                    if limit == 0:
                        break
            if limit == 0:
                break
    return arr

def login_and_submit_files(username: str, password: str):
    session = requests.Session()
    login_url = 'https://code.ptit.edu.vn/login'
    submit_url = 'https://code.ptit.edu.vn/student/solution'
    
    try:
        login_page = session.get(login_url)
        if login_page.status_code != 200:
            raise Exception(f"Failed to load login page: {login_page.status_code}")
        
        login_soup = BeautifulSoup(login_page.text, 'html.parser')
        csrf_token_input = login_soup.find('input', {'name': '_token'})
        if not csrf_token_input:
            raise Exception("CSRF token not found on login page.")
        csrf_token = csrf_token_input['value']
        
        login_data = {
            '_token': csrf_token,
            'username': username,
            'password': password
        }
        
        login_response = session.post(login_url, data=login_data)
        if login_response.status_code != 200:
            raise Exception("Login failed. Please check your credentials.")
        
        print("Login successful!")
        
        client = MongoClient('mongodb://localhost:27017/')
        db = client['Autosub_PTIT']
        collection_questions = db['questionsJava']
        collection_files = db['fs.chunks']
        
        url = f"{DOMAIN}/not-done-files?username={username}&password={password}"
        response = requests.get(url)
        if response.status_code != 200:
            raise Exception(f"Failed to fetch files: {response.status_code}")
        
        json_data = response.json()
        
        for item in json_data['files']:
            data = collection_questions.find_one({'alias': item})
            if not data:
                print(f"No data found for alias: {item}")
                continue

            file_id = data['file_id']
            name = data['name']
            file = collection_files.find_one({'files_id': ObjectId(file_id)})
            if not file:
                print(f"No file found for file_id: {file_id}")
                continue
            
            file_content = file['data']
            
            submit_page_url = f'https://code.ptit.edu.vn/student/question/{item}'
            submit_page = session.get(submit_page_url)
            if submit_page.status_code != 200:
                raise Exception(f"Failed to load submit page: {submit_page.status_code}")
            
            submit_soup = BeautifulSoup(submit_page.text, 'html.parser')
            submit_csrf_token_input = submit_soup.find('input', {'name': '_token'})
            if not submit_csrf_token_input:
                raise Exception("Submit CSRF token not found on submit page.")
            submit_csrf_token = submit_csrf_token_input['value']
            
            files = {
                'code_file': (name, file_content, 'application/octet-stream')
            }
            data = {
                '_token': submit_csrf_token,
                'question': item,
                'compiler': '3' 
            }
            submit_response = session.post(submit_url, data=data, files=files)
            if submit_response.status_code != 200:
                raise Exception(f"Failed to submit file: {submit_response.status_code}")
            
            result_soup = BeautifulSoup(submit_response.text, 'html.parser')
            result_message = result_soup.find('div', {'class': 'alert'})
            if result_message:
                print(result_message.text.strip())
            else:
                print("File submitted successfully!")
            time.sleep(5)
                
    except Exception as e:
        print(f"An error occurred: {e}")

@app.get("/")
def read_root():
    return {"message": "Welcome to PTIT Code API"}

@app.get("/not-done")
def not_done_questions(username: str, password: str):
    xsrf_token, ptit_code_session = login(username, password)
    total_not_done_questions = get_len_not_done_question(xsrf_token, ptit_code_session)
    return {"not_done": total_not_done_questions}
    
@app.get("/not-done-files")
def not_done_files(username: str, password: str, limit: int = 30):
    xsrf_token, ptit_code_session = login(username, password)
    files = get_files_not_done(xsrf_token, ptit_code_session, limit)
    return {"files": files}


@app.get("/check-account")
def check_account_endpoint(username: str, password: str):
    if check_account(username, password):
        return {"status": "Login successful"}
    else:
        raise HTTPException(status_code=401, detail="Login failed")

@app.post("/submit-files")
def login_and_submit_files_endpoint(username: str, password: str):
    login_and_submit_files(username, password)
    return {"message": "Files submitted successfully!"}
