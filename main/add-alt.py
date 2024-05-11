from langchain.agents import initialize_agent
from langchain.chat_models import ChatOllama
from langchain.callbacks import StreamingStdOutCallbackHandler
from langchain.chains.conversation.memory import ConversationBufferWindowMemory

from tools import ImageCaptionTool, ObjectDetectionTool

from transformers import BlipProcessor, BlipForConditionalGeneration, DetrImageProcessor, DetrForObjectDetection
from PIL import Image
import torch

import os
import json
import tempfile

def get_image_caption(image_path):
    """
    Generates a short caption for the provided image.

    Args:
        image_path (str): The path to the image file.

    Returns:
        str: A string representing the caption for the image.
    """
    image = Image.open(image_path).convert('RGB')

    model_name = "Salesforce/blip-image-captioning-large"
    device = "cpu"  # cuda

    processor = BlipProcessor.from_pretrained(model_name)
    model = BlipForConditionalGeneration.from_pretrained(model_name).to(device)

    inputs = processor(image, return_tensors='pt').to(device)
    output = model.generate(**inputs, max_new_tokens=20)

    caption = processor.decode(output[0], skip_special_tokens=True)

    return caption

def detect_objects(image_path):
    """
    Detects objects in the provided image.

    Args:
        image_path (str): The path to the image file.

    Returns:
        str: A string with all the detected objects. Each object as '[x1, x2, y1, y2, class_name, confindence_score]'.
    """
    image = Image.open(image_path).convert('RGB')

    processor = DetrImageProcessor.from_pretrained("facebook/detr-resnet-50")
    model = DetrForObjectDetection.from_pretrained("facebook/detr-resnet-50")

    inputs = processor(images=image, return_tensors="pt")
    outputs = model(**inputs)

    # convert outputs (bounding boxes and class logits) to COCO API
    # let's only keep detections with score > 0.9
    target_sizes = torch.tensor([image.size[::-1]])
    results = processor.post_process_object_detection(outputs, target_sizes=target_sizes, threshold=0.9)[0]

    detections = ""
    for score, label, box in zip(results["scores"], results["labels"], results["boxes"]):
        detections += '[{}, {}, {}, {}]'.format(int(box[0]), int(box[1]), int(box[2]), int(box[3]))
        detections += ' {}'.format(model.config.id2label[int(label)])
        detections += ' {}\n'.format(float(score))

    return detections


tools = [ImageCaptionTool(), ObjectDetectionTool()]

conversational_memory = ConversationBufferWindowMemory(
    memory_key='chat_history',
    k=5,
    return_messages=True
)

llm = ChatOllama(
    model = "llama3:8b",
    temperature=0.1,
    streaming=True,
    callbacks=[StreamingStdOutCallbackHandler()]
)

agent = initialize_agent(
    agent="chat-conversational-react-description",
    tools=tools,
    llm=llm,
    max_iterations=5,
    verbose=True,
    memory=conversational_memory,
    early_stopping_method='generate'
)

agent = initialize_agent(
    agent="chat-conversational-react-description",
    tools=tools,
    llm=llm,
    max_iterations=5,
    verbose=True,
    memory=conversational_memory,
    early_stopping_method='generate'
)

context = "very happy situation" # 주변 div의 context 내용이 포함됨
language = "korean" # 확장 프로그램에서 언어 설정 가능토록 할 것.
# user_question = f"Describe the visual elements of the image in one line based {context}. and translate to {language}"
user_question = f"Describe the visual elements of the image in one line based {context}."

if not os.path.exists('responses/'):
    os.makedirs('responses/')

image_files = os.listdir('imgs/')

# todo
# 이 파트 함수든 뭐든으로 만들어서 깔끔하게 정리

for image_name in image_files:
    tools = [ImageCaptionTool(), ObjectDetectionTool()]

    original_image_path = os.path.join('imgs', image_name)
    print("---original img path:", original_image_path)

    if not os.path.exists(original_image_path):
        print(f"---can't find: {original_image_path}")
        continue

    try:
        with Image.open(original_image_path) as img:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp:
                img.save(tmp.name)
                image_path = tmp.name
                print("---temp img path:", image_path)
                try:
                    response = agent.run(f'{user_question}, image path: {image_path}')
                except FileNotFoundError as e:
                    print(f"can't open: {e}")   
    except FileNotFoundError as e:
        print(f"can't open: {e}")
        continue

    print("---response:", response)

    response_file_path = os.path.join('responses', "output.json")
    
    if os.path.exists(response_file_path):
        with open(response_file_path, 'r', encoding='utf-8') as file:
            try:
                data = json.load(file)
            except json.JSONDecodeError:
                data = {}
    else:
        data = {}
    
    data[image_name] = {"image_name": image_name, "response": response}
    
    with open(response_file_path, 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

os.remove("__pycache__/tools.cpython-311.pyc")
os.remove("responses/output.json")
os.remove("imgs")
######################################
# 이런 방식으로 이름 넣으면 될수도
# f.write(file.getbuffer())
# image_path = f.name
#