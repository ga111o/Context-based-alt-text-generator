from flask import Flask, request, Response, make_response
import os
import requests
from bs4 import BeautifulSoup
from mimetypes import guess_extension
from urllib.parse import urljoin, urlparse
import subprocess
import time
from requests.exceptions import ConnectionError

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
    url = request.args.get('url', default='', type=str)
    output_folder = "./imgs"

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    try:
        response = requests.get(url)
        if response.status_code != 200:
            return "connection error 1"
    except ConnectionError:
        return "connection error 2"

    soup = BeautifulSoup(response.content, "html.parser")
    img_tags = soup.find_all("img")

    downloaded_files = set()  

    for i, img in enumerate(img_tags):
        if not img.has_attr('alt'):
            img_url = img.get("src")
            if img_url:
                full_img_url = urljoin(url, img_url)
                img_name = os.path.basename(urlparse(full_img_url).path) 

                # original_img_name = img_name
                # count = 1
                # while img_name in downloaded_files:
                #     name, ext = os.path.splitext(original_img_name)
                #     img_name = f"{name}_{count}{ext}"
                #     count += 1

                downloaded_files.add(img_name)

                try:
                    img_response = requests.get(full_img_url, stream=True)
                    if img_response.status_code == 200:
                        img_path = os.path.join(output_folder, img_name)
                        with open(img_path, "wb") as img_file:
                            for chunk in img_response.iter_content(chunk_size=8192):
                                img_file.write(chunk)
                        print(f"download: {img_path}")
                except ConnectionError:
                    print(f"failed download image: {img_url}")

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
    
if __name__ == '__main__':
    app.run(debug=True, port=9990)
