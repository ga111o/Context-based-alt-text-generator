from tools import ImageCaptionTool
from settings import agent
from PIL import Image
import os
import json
import tempfile
import sys
import DEBUG

if len(sys.argv) > 1:
    session = sys.argv[1]

with open(f'./source/{session}/responses/input.json', 'r', encoding='utf-8') as file:
    image_info = json.load(file)

image_files = list(image_info.keys())

# todo
# 이 파트 함수든 뭐든으로 만들어서 깔끔하게 정리
for image_name in image_files:
    original_image_path = os.path.join("source", session, "imgs", image_name)

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

                    user_question = f"image's article title is {title} and image's context is {context}."
                    response = agent.run(f"{user_question}, image path: {image_path}")

                except FileNotFoundError as e:
                    print(f"can't open: {e}")
    except FileNotFoundError as e:
        print(f"can't open: {e}")
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
