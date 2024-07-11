from flask import Flask, request, Response, make_response, jsonify
import os
import requests
import subprocess
import time
from requests.exceptions import ConnectionError
from flask import Flask, request
from flask_cors import CORS
import DEBUG
from flask import Flask
import logging
import os
from io import StringIO
from datetime import datetime, timedelta

app = Flask(__name__)
CORS(app)

log_buffer = StringIO()
handler = logging.StreamHandler(log_buffer)
handler.setLevel(logging.INFO)

formatter = logging.Formatter('%(asctime)s - %(message)s')
handler.setFormatter(formatter)

wz_log = logging.getLogger('werkzeug')
wz_log.setLevel(logging.INFO)
wz_log.addHandler(handler)

app.logger.setLevel(logging.INFO)
app.logger.addHandler(handler)

logs_list = []
max_time = timedelta(minutes=3)

@app.before_request
def before_request():
    current_time = datetime.now()

    log_buffer.seek(0)
    new_logs = log_buffer.read()
    log_buffer.truncate(0)
    log_buffer.seek(0)
    
    if new_logs:
        for log_line in new_logs.strip().split('\n'):
            log_time_str = log_line.split(' - ')[0]
            log_time = datetime.strptime(log_time_str, '%Y-%m-%d %H:%M:%S,%f')
            logs_list.append((log_time, log_line))
    
    logs_list[:] = [(log_time, log) for log_time, log in logs_list if current_time - log_time <= max_time]


api_keys = {}

@app.route("/")
def check_working():
	return "working..."

@app.route("/logs")
def get_logs():
    current_time = datetime.now()

    logs_list[:] = [(log_time, log) for log_time, log in logs_list if current_time - log_time <= max_time]
    
    logs = '\n'.join(log for _, log in logs_list)
    return Response(logs, mimetype='text/plain')

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
        
        print(f" | {session} | Received API Key: {api_key}")
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
    url = request.args.get("url", default="", type=str)
    session = request.args.get("session", default="", type=str)
    model = request.args.get("model", default="", type=str)
    language = request.args.get("language", default="", type=str)
    if DEBUG.PRINT_LOG_BOOLEN:
        print(f" | {session} | url: {url} | model: {model} | language: {language}")

    img_folder = f"./source/{session}/imgs"
    response_folder = f"./source/{session}/responses"

    if not os.path.exists(img_folder):
        os.makedirs(img_folder)
    if not os.path.exists(response_folder):
        os.makedirs(response_folder)

    try:
        response = requests.get(url)
        if response.status_code != 200:
            print(" | {session} | ERROR: response.status_code != 200")
    except ConnectionError as e:
        print(f" | {session} | ERROR: connection error 2: {e}")

    language = request.args.get("language", default="", type=str)
    title = request.args.get("title", default="", type=str)

    if DEBUG.PRINT_LOG_BOOLEN:
        print(f" | {session} | call download-img.py")

    subprocess.call(["python", "download-img.py", session, url, language, title])
    
    if model == "caption":
        if DEBUG.PRINT_LOG_BOOLEN:
            print(f" | {session} | call generate-alt-only-caption-model.py")
        subprocess.call(["python", "generate-alt-only-caption-model.py", session])
        if DEBUG.PRINT_LOG_BOOLEN:
            print(f" | {session} | done generate-alt-only-caption-model.py\n")
    elif model == "llm":
        if DEBUG.PRINT_LOG_BOOLEN:
            print(f" | {session} | call generate-alt.py")
        subprocess.call(["python", "generate-alt.py", session])
        if DEBUG.PRINT_LOG_BOOLEN:
            print(f" | {session} | done call generate-alt.py\n")
    elif model == "lmm":
        if DEBUG.PRINT_LOG_BOOLEN:
            print(f" | {session} | call generate-alt-lmm.py")
        subprocess.call(["python", "generate-alt-lmm.py", session])
        if DEBUG.PRINT_LOG_BOOLEN:
            print(f" | {session} | done call generate-alt-lmm.py\n")
    else:
        if DEBUG.PRINT_LOG_BOOLEN:
            print(f" | {session} | call generate-alt-only-caption-model.py")
        subprocess.call(["python", "generate-alt-only-caption-model.py", session])
        if DEBUG.PRINT_LOG_BOOLEN:
            print(f" | {session} | done generate-alt-only-caption-model.py\n")

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
    app.run(port=9990)

