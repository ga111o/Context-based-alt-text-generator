from flask import Flask, request, Response, make_response
import os
import requests
from bs4 import BeautifulSoup
from mimetypes import guess_extension
from urllib.parse import urljoin, urlparse
import subprocess
import time
from requests.exceptions import ConnectionError
import shutil
import json

from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/')
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
# 함수 너무 길어지는 거 나눠야할듯
@app.route('/url')
def get_url_n_img():
    if os.path.exists("imgs/"): # 이건 여기가 아니라 다른 곳에서 관리해야 할 거 같은데
        shutil.rmtree("imgs/")
    if os.path.exists("__pycache__/tools.cpython-311.pyc"):
        os.remove("__pycache__/tools.cpython-311.pyc")
    if os.path.exists("responses/"): # 이건 여기가 아니라 다른 곳에서 관리해야 할 거 같은데
        shutil.rmtree("responses/")
    url = request.args.get('url', default='', type=str)
    img_folder = "./imgs"
    response_folder = "./responses"

    if not os.path.exists(img_folder):
        os.makedirs(img_folder)

    if not os.path.exists(response_folder):
        os.makedirs(response_folder)

    response_data = {}

    try:
        response = requests.get(url)
        if response.status_code != 200:
            print("connection error 1")
    except ConnectionError:
        print("connection error 2")

    soup = BeautifulSoup(response.content, "html.parser")
    img_tags = soup.find_all("img")

    downloaded_files = set()  

    for i, img in enumerate(img_tags):
        if not img.has_attr('alt'):
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
                        print(f"download: {img_path}")

                        # 상위 태그 내의 모든 텍스트를 넣는 게 맞나 싶음..
                        # 근데 이거 말고는 딱히 방법이 안보이기도 하고..
                        context = img.parent.get_text(strip=True)
                        response_data[img_name] = {
                            "image_path": img_path,
                            "context": context,
                            "language": request.args.get('language', default='', type=str)
                        }
                except ConnectionError:
                    print(f"failed download image: {img_url}")

    with open('./responses/input.json', 'w', encoding='utf-8') as json_file:
        json.dump(response_data, json_file, indent=4, ensure_ascii=False)

    subprocess.call(['python', 'add-alt.py'])

    if wait_for_file('./responses/output.json'):
        return f"url: {url}, download done & generate output.json"
    else:
        return "failed(timeout)"

@app.route('/output')
def output_json():
    try:
        with open('./responses/output.json', 'r', encoding='utf-8') as file:
            data = file.read()
        return Response(data, mimetype='application/json')
    except FileNotFoundError:
        return make_response('', 404)
    
@app.route('/input')
def intput_json():
    try:
        with open('./responses/input.json', 'r', encoding='utf-8') as file:
            data = file.read()
        return Response(data, mimetype='application/json')
    except FileNotFoundError:
        return make_response('', 404)
    
if __name__ == '__main__':
    app.run(debug=True, port=9990)
