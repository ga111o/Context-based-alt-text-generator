from flask import Flask, request, Response, make_response, jsonify
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

api_keys = {}

@app.route("/")
def check_working():
	return "working..."

import os

@app.route('/apikey', methods=['POST'])
def receive_api_key():
    data = request.get_json()
    api_key = data.get('apiKey')
    session = data.get('session')
    
    if api_key and session:
        directory = f"./source/{session}/responses"
        filepath = os.path.join(directory, 'key')
        
        if not os.path.exists(directory):
            os.makedirs(directory)
        
        with open(filepath, 'w') as file:
            file.write(api_key)
        
        print(f"Received API Key: {api_key}")
        print(f"Session ID: {session}")
        return jsonify({'apiKey': api_key})
    else:
        return jsonify({'error': 'No API Key or Session provided'}), 400


def wait_for_file(file_path, timeout=60):
	start_time = time.time()
	while not os.path.exists(file_path):
		time.sleep(1)
		if time.time() - start_time > timeout:
			return False
	return True

@app.route("/url")
async def get_url_n_img():
    print(f"==============full url: {request.args}")
    url = request.args.get("url", default="", type=str)
    session = request.args.get("session", default="", type=str)
    model = request.args.get("model", default="", type=str)
    language = request.args.get("language", default="", type=str)

    img_folder = f"./source/{session}/imgs"
    response_folder = f"./source/{session}/responses"

    if not os.path.exists(img_folder):
        os.makedirs(img_folder)
    if not os.path.exists(response_folder):
        os.makedirs(response_folder)

    try:
        response = requests.get(url)
        if response.status_code != 200:
            print("========== ERROR: response.status_code != 200")
    except ConnectionError as e:
        print(f"========== ERROR: connection error 2: {e}")

    language = request.args.get("language", default="", type=str)
    title = request.args.get("title", default="", type=str)

    print(f"================== at server, language: {language}")

    subprocess.call(["python", "download-img.py", session, url, language, title])
    
    if model == "caption":
        print("only caption model")
        subprocess.call(["python", "generate-alt-only-caption-model.py", session])
    elif model == "llm":
        print("caption model + llm")
        subprocess.call(["python", "generate-alt.py", session])
    elif model == "lmm":
        print("lmm")
        subprocess.call(["python", "generate-alt-lmm.py", session])
    else:
        subprocess.call(["python", "generate-alt-only-caption-model.py", session])

    if DEBUG.DELETE_DATABASE:
         os.remove("./database/images.db")

    if wait_for_file(f"./{response_folder}/output.json"):
        if(DEBUG.PRINT_LOG_BOOLEN):
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
    # from waitress import serve
    # serve(app, port=9990)
    app.run(debug=True, port=9990)

