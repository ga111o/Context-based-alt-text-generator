from flask import Flask, request, Response, make_response
import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import subprocess
import time
from requests.exceptions import ConnectionError
import json
from flask import Flask, request
from flask_cors import CORS
from sqlalchemy import null
import DEBUG

app = Flask(__name__)
CORS(app)

DEBUG_DOWNLOADIMG = False

@app.route("/")
def working():
	return "working..."

def wait_for_file(file_path, timeout=60):
	start_time = time.time()
	while not os.path.exists(file_path):
		time.sleep(1)
		if time.time() - start_time > timeout:
			return False
	return True

# todo
# func is tooo long, split required
@app.route("/url")
async def get_url_n_img():
    url = request.args.get("url", default="", type=str)
    session = request.args.get("session", default="", type=str)

    img_folder = f"./source/{session}/imgs"
    response_folder = f"./source/{session}/responses"

    if not os.path.exists(img_folder):
        os.makedirs(img_folder)
    if not os.path.exists(response_folder):
        os.makedirs(response_folder)

    response_data = {}

    try:
        response = requests.get(url)
        if response.status_code != 200:
            print("========== ERROR: response.status_code != 200")
    except ConnectionError:
        print("========== ERROR: connection error 2")

    if DEBUG_DOWNLOADIMG:
        soup = BeautifulSoup(response.content, "html.parser")
        img_tags = soup.find_all("img")

        downloaded_files = set()  

        for i, img in enumerate(img_tags):
            if not img.has_attr("alt"):
                img_url = img.get("src")
                if img_url:
                    full_img_url = urljoin(url, img_url)
                    img_name = os.path.basename(urlparse(full_img_url).path) 

                    downloaded_files.add(img_name)

                    try:
                        img_response = requests.get(full_img_url, stream=True)
                        if img_response.status_code == 200:
                            img_path = os.path.join(img_folder, img_name)
                            with open(img_path, "wb") as img_file:
                                for chunk in img_response.iter_content(chunk_size=8192):
                                    img_file.write(chunk)
                            if(DEBUG.PRINT_LOG_BOOLEN):
                                print(f"download: {img_path}")
                            
                            context = img.parent.get_text(strip=True)
                            response_data[img_name] = {
                                "image_path": img_path,
                                "context": context,
                                "language": request.args.get("language", default="", type=str),
                                "title": request.args.get("title", default="", type=str)
                            }
                    except ConnectionError:
                        if(DEBUG.PRINT_LOG_BOOLEN):
                            print(f"failed download image: {img_url}")
        
        with open(f"./{response_folder}/input.json", "w", encoding="utf-8") as json_file:
            json.dump(response_data, json_file, indent=4, ensure_ascii=False)
                        
    language = request.args.get("language", default="", type=str)
    title = request.args.get("title", default="", type=str)
    
    subprocess.call(["python", "download-img.py", session, url, language, title])
    subprocess.call(["python", "add-alt.py", session])

    if wait_for_file(f"./{response_folder}/output.json"):
        if(DEBUG.PRINT_LOG_BOOLEN):
            print("확장 프로그램에게 '`output.json`이 생겼어요!'를 알려주는 방법이 뭐가 있을까..")
            print("`output.json`이 업데이트 되었다는 것도 체크 가능한데, 업데이트 되었다는 걸 알려주는 방법을 모르겠네...")
            return f"url: {url}, download done & generate output.json"
    else:
        return "failed(timeout)"

@app.route(f"/<user_input>/output")
def output_json(user_input):
    try:    
        with open(f"./source/{user_input}/responses/output.json", "r", encoding="utf-8") as file:
            data = file.read()
        return Response(data, mimetype="application/json")
    except FileNotFoundError:
        return make_response("session not exist", 450)
    
@app.route(f"/<user_input>/input")
def intput_json(user_input):
    try:
        with open(f"./source/{user_input}/responses/input.json", "r", encoding="utf-8") as file:
            data = file.read()
        return Response(data, mimetype="application/json")
    except FileNotFoundError:
        return make_response("session not exist", 450)
    
if __name__ == "__main__":
    from waitress import serve
    # serve(app, port=9990)
    app.run(debug=True, port=9990)

