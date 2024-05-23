from tools import ImageCaptionTool, ObjectDetectionTool
from settings import agent
from PIL import Image

import os
import json
import tempfile
import sys

DEBUG = True

tools = [ImageCaptionTool(), ObjectDetectionTool()]

if len(sys.argv) > 1:
    session = sys.argv[1]
    print("===========================================\nsession:", session)
else:
    print("=================\nsession 전달 X \n==================")


with open(f'./source/{session}/responses/input.json', 'r', encoding='utf-8') as file:
    image_info = json.load(file)

image_files = list(image_info.keys())

if DEBUG:
    test_path = f'./source/{session}/responses/'
    os.makedirs(test_path, exist_ok=True)
    with open(os.path.join(test_path, f'test1-{session}'), 'w') as f:
        pass

# todo
# 이 파트 함수든 뭐든으로 만들어서 깔끔하게 정리
for image_name in image_files:
    original_image_path = os.path.join("source", session, "imgs", image_name)
    print("---original img path:", original_image_path)

    if not os.path.exists(original_image_path):
        print(f"---can't find: {original_image_path}")
        continue

    if DEBUG:
        test_path = f'./source/{session}/responses/'
        os.makedirs(test_path, exist_ok=True)
        with open(os.path.join(test_path, f'test2-{session}'), 'w') as f:
            pass

    try:
        with Image.open(original_image_path) as img:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
                img.save(tmp.name)
                image_path = tmp.name
                print("---temp img path:", image_path)
                
                if DEBUG:
                    test_path = f'./source/{session}/responses/'
                    os.makedirs(test_path, exist_ok=True)
                    with open(os.path.join(test_path, f'test2.1-{session}'), 'w') as f:
                        pass

                try:
                    context = image_info[image_name]["context"]
                    language = image_info[image_name]["language"]
                    
                    user_question = f"Describe the visual elements of the image in one line based {context}. and translate to {language}"
                    response = agent.run(f"{user_question}, image path: {image_path}")
                    
                    if DEBUG:
                        test_path = f'./source/{session}/responses/'
                        os.makedirs(test_path, exist_ok=True)
                        with open(os.path.join(test_path, f'test2.2-{session}'), 'w') as f:
                            pass

                except FileNotFoundError as e:
                    print(f"can't open: {e}")
    except FileNotFoundError as e:
        print(f"can't open: {e}")
        continue
    
    if DEBUG:
        test_path = f'./source/{session}/responses/'
        os.makedirs(test_path, exist_ok=True)
        with open(os.path.join(test_path, f'test3-{session}'), 'w') as f:
            pass
    
    print("---response:", response)
    
    response_file_path = os.path.join("source", session, "responses", "output.json")
    
    if os.path.exists(response_file_path):
        with open(response_file_path, "r", encoding="utf-8") as file:
            try:
                data = json.load(file)
            except json.JSONDecodeError:
                data = {}
    else:
        data = {}

    if DEBUG:
        test_path = f'./source/{session}/responses/'
        os.makedirs(test_path, exist_ok=True)
        with open(os.path.join(test_path, f'test4-{session}'), 'w') as f:
            pass
    
    data[image_name] = {"image_name": image_name, "response": response}
    
    with open(response_file_path, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)
