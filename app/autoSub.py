import requests
from bs4 import BeautifulSoup
from pymongo import MongoClient

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
        
        url = f"http://127.0.0.1:8000/not-done-files?username={username}&password={password}"
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