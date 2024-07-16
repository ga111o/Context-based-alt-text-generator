from tools import ImageCaptionTool
from tools import ImageCaptionTool
from PIL import Image
import os
import json
import tempfile
import sys
from langchain.agents import initialize_agent, AgentType
from langchain.chat_models import ChatOllama, ChatOpenAI
from langchain.callbacks import StreamingStdOutCallbackHandler
from tools import ImageCaptionTool, ObjectDetectionTool, TranslateTool
import DEBUG
import hashlib
import sqlite3
from langchain.schema import SystemMessage
from openai import OpenAI

if len(sys.argv) > 1:
    session = sys.argv[1]

if DEBUG.PRINT_LOG_BOOLEN:
    print(f" | {session} |-- in the generate-alt-object.py")

with open(f'./source/{session}/responses/input.json', 'r', encoding='utf-8') as file:
    image_info = json.load(file)

image_files = list(image_info.keys())

key_path = f'./source/{session}/responses/key'
with open(key_path, 'r', encoding='utf-8') as file:
    api_key = file.read()

db_folder = "./database"

db_path = os.path.join(db_folder, "images.db")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

client = OpenAI()


tools = [ImageCaptionTool(), ObjectDetectionTool()]

def get_image_hash(image_path):
    hasher = hashlib.sha256()
    with open(image_path, 'rb') as img_file:
        buf = img_file.read()
        hasher.update(buf)
    return hasher.hexdigest()

def check_image_in_db(conn, image_name, original_url, context, language, image_hash):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, object_output FROM images WHERE image_name=? AND original_url=? AND context=? AND language=? AND hash=?
    """, (image_name, original_url, context, language, image_hash))
    return cursor.fetchone()

def update_image_output(conn, image_id, output):
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE images SET object_output=? WHERE id=?
    """, (output, image_id))
    conn.commit()

def insert_image(conn, image_name, original_url, img_path, context, language, title, image_hash, output):
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO images (image_name, original_url, img_path, context, language, title, hash, object_output)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (image_name, original_url, img_path, context, language, title, image_hash, output))
    conn.commit()

def invoke_agent(language, title, context, url):

    import base64
    import requests

    translations = {
        "Korean": f"이미지 속 객체들을 쉼표로 구분해서 알려줘. 객체 이외의 대답은 하면 안돼. 그리고 객체들을 {language}로 번역해.",
        "Japanese": f"画像に写っているものをコンマで区切って教えてください。次に、そのオブジェクトを{language}に訳してください。",
        "Chinese": f"告诉我图片中的物体，用逗号分隔。然后将这些物体翻译成{language}。",
        "Spanish": f"Dime los objetos de la imagen, separados por comas. A continuación, traduce los objetos a {language}."
    }

    user_question = translations.get(language, f"Tell me the objects in the image, separated by commas. Then translate the objects into {language}.")

    if language == "English":
        question = user_question
    else:
        question = user_question
    
    def encode_image(image_path):
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    image_path = f"{url}"

    base64_image = encode_image(image_path)

    headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {api_key}"
    }

    payload = {
    "model": "gpt-4o",
    "temperature": 0.1,
    "messages": [
        {
        "role": "user",
        "content": [
            {
            "type": "text",
            "text": question
            },
            {
            "type": "image_url",
            "image_url": {
                "url": f"data:image/jpeg;base64,{base64_image}"
            }
            }
        ]
        }
    ],
    }

    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)

    out = response.json()
    if DEBUG.PRINT_LOG_BOOLEN:
        print(f" | {session} |---- {out['choices'][0]['message']['content']}, token: {out['usage']['total_tokens']}")

    return out['choices'][0]['message']['content']




image_info_path = os.path.join("source", session, "responses", "input.json")

with open(image_info_path, "r", encoding="utf-8") as file:
    image_info = json.load(file)

for image_name, image_data in image_info.items():
    original_image_path = image_data["image_path"]

    if not os.path.exists(original_image_path):
        continue

    try:
        with Image.open(original_image_path) as img:
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")

            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
                img.save(tmp.name)
                image_path = tmp.name

                try:
                    context = image_info[image_name]["context"]
                    language = image_info[image_name]["language"]
                    title = image_info[image_name]["title"]
                    original_url = image_data["original_url"]

                    image_hash = get_image_hash(image_path)  
                    
                    db_result = check_image_in_db(conn, image_name, original_url, context, language, image_hash)
                    
                    if db_result:
                        image_id, db_output = db_result
                        if db_output:
                            response = {"output": db_output}
                            if DEBUG.PRINT_LOG_BOOLEN:
                                print(f" | {session} |---- already exist object alt text {image_name}")

                        else:
                            response = invoke_agent(language, title, context, image_path)
                            update_image_output(conn, image_id, response)  
                    else:
                        response = invoke_agent(language, title, context, image_path)
                        insert_image(conn, image_name, original_url, image_path, context, language, title, image_hash, response)  

                except FileNotFoundError as e:
                    print(f" | {session} |---- can't open: {e}")
    except FileNotFoundError as e:
        print(f" | {session} |---- can't open: {e}")
        continue
    
    response_file_path = os.path.join("source", session, "responses", "output.json")
    
    if os.path.exists(response_file_path):
        with open(response_file_path, "r", encoding="utf-8") as file:
            try:
                data = json.load(file)
            except json.JSONDecodeError:
                data = {}
    else:
        data = {}
    
    data[image_name] = {"image_name": image_name, "response": response}
    
    with open(response_file_path, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

conn.close()