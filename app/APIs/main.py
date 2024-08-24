import os
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from typing import Tuple, Optional

load_dotenv()

app = FastAPI()

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
    
    return login_response.status_code == 200 and login_response.url == 'https://code.ptit.edu.vn/student/question'

def login(username: str, password: str) -> Tuple[str, str]:
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
    
    if login_response.status_code != 200:
        raise HTTPException(status_code=401, detail="Login failed")

    xsrf_token, ptit_code_session = login_response.cookies.get_dict().values()
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

@app.get("/")
def read_root():
    try:
        return {"message": "Welcome to PTIT Code API"}
    except Exception as e:
        print(f"Error occurred: {e}")
        raise HTTPException(status_code=500, detail="An error occurred")
    
@app.get("/not-done")
def not_done_questions(username: Optional[str] = None, password: Optional[str] = None):
    if not username or not password:
        raise HTTPException(status_code=400, detail="Username and password are required")

    xsrf_token, ptit_code_session = login(username, password)
    total_not_done_questions = get_len_not_done_question(xsrf_token, ptit_code_session)
    return {"not_done": total_not_done_questions}

@app.get("/check-account")
def check_account_endpoint(username: Optional[str] = None, password: Optional[str] = None):
    if not username or not password:
        raise HTTPException(status_code=400, detail="Username and password are required")

    if check_account(username, password):
        return {"status": "Login successful"}
    else:
        raise HTTPException(status_code=401, detail="Login failed")
