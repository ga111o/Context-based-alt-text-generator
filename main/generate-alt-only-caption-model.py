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

if len(sys.argv) > 1:
    session = sys.argv[1]

if DEBUG.PRINT_LOG_BOOLEN:
    print(f" | {session} |-- in the generate-alt-only-caption-model.py")


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


if DEBUG.SELECT_LLM == 1:
    llm = ChatOpenAI(
        model="gpt-3.5-turbo",
        temperature=0.1,
        streaming=True,
        api_key=api_key,
        callbacks=[StreamingStdOutCallbackHandler()],
    )
elif DEBUG.SELECT_LLM == 2:
    llm = ChatOllama(
        model = "llama3:8b",    
        temperature=0.1,
        streaming=True,
        callbacks=[StreamingStdOutCallbackHandler()],
    )

tools = [ImageCaptionTool(), ObjectDetectionTool()]

agent = initialize_agent(
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    tools=tools,
    llm=llm,
    max_iterations=5,
    verbose=DEBUG.VERBOSE,
    early_stopping_method="generate",
    agent_kwargs={
        "system_message": SystemMessage(
            content="""
            You are a model that translates descriptions of images into other languages.

            You don't use the tool and translate manually.
        """
        )
    },
    )

def get_image_hash(image_path):
    hasher = hashlib.sha256()
    with open(image_path, 'rb') as img_file:
        buf = img_file.read()
        hasher.update(buf)
    return hasher.hexdigest()

def check_image_in_db(conn, image_name, original_url, context, language, image_hash):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, caption_output FROM images WHERE image_name=? AND original_url=? AND context=? AND language=? AND hash=?
    """, (image_name, original_url, context, language, image_hash))
    return cursor.fetchone()

def update_image_output(conn, image_id, output):
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE images SET caption_output=? WHERE id=?
    """, (output, image_id))
    conn.commit()

def insert_image(conn, image_name, original_url, img_path, context, language, title, image_hash, output):
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO images (image_name, original_url, img_path, context, language, title, hash, caption_output)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (image_name, original_url, img_path, context, language, title, image_hash, output))
    conn.commit()

def invoke_agent(language, image_path):
    translations = {
        "Korean": "Image captioner를 사용하고, Image captioner의 답변을 한국어로 번역해. 단, 번역을 할 때에는 도구를 사용하지 말고 직접 번역해야 돼.",
        "Japanese": "Image captionerを使用し、Image captionerの回答を韓国語に翻訳してください。",
        "Chinese": "使用图像标题器，并将图像标题器的答案翻译成您的语言。",
        "Spanish": "Utiliza un subtitulador de imágenes y traduce la respuesta del subtitulador a tu idioma."
    }

    user_question = translations.get(language, f"Use an image captioner and translate the image captioner's answer into your language.")
    
    if language == "English":
        if DEBUG.PRINT_LOG_BOOLEN:
            print(f" | {session} |---- {user_question}, image path: {image_path}")
        return agent.invoke(f"{user_question}, image path: {image_path}")
    else:
        if DEBUG.PRINT_LOG_BOOLEN:
            print(f" | {session} |---- {user_question}, image path: {image_path}")
        return agent.invoke(f"{user_question}, image path: {image_path}")


image_info_path = os.path.join("source", session, "responses", "input.json")

with open(image_info_path, "r", encoding="utf-8") as file:
    image_info = json.load(file)

for image_name, image_data in image_info.items():
    original_image_path = image_data["image_path"]

    if not os.path.exists(original_image_path):
        continue

    try:
        with Image.open(original_image_path) as img:
            if img.mode == "RGBA":
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
                                print(f" | {session} |---- already exist caption model alt text {image_name}")
                        else:
                            response = invoke_agent(language, image_path)
                            update_image_output(conn, image_id, response['output'])  
                    else:
                        response = invoke_agent(language, image_path)
                        insert_image(conn, image_name, original_url, image_path, context, language, title, image_hash, response['output'])  

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
    
    data[image_name] = {"image_name": image_name, "response": response['output']}
    
    with open(response_file_path, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

conn.close()