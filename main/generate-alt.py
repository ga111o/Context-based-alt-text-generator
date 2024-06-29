from tools import ImageCaptionTool
from PIL import Image
import os
import json
import tempfile
import sys
import DEBUG
from langchain.agents import initialize_agent, AgentType
from langchain.chat_models import ChatOllama, ChatOpenAI
from langchain.callbacks import StreamingStdOutCallbackHandler
from langchain.chains.conversation.memory import ConversationBufferWindowMemory
from tools import ImageCaptionTool, ObjectDetectionTool
import DEBUG


if len(sys.argv) > 1:
    session = sys.argv[1]

with open(f'./source/{session}/responses/input.json', 'r', encoding='utf-8') as file:
    image_info = json.load(file)

image_files = list(image_info.keys())

key_path = f'./source/{session}/responses/key'
with open(key_path, 'r', encoding='utf-8') as file:
    api_key = file.read()

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

conversational_memory = ConversationBufferWindowMemory(
    memory_key="chat_history",
    k=0,
    return_messages=True
)

tools = [ImageCaptionTool(), ObjectDetectionTool()]

agent = initialize_agent(
    # agent="chat-conversational-react-description",
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    tools=tools,
    llm=llm,
    max_iterations=5,
    verbose=DEBUG.VERBOSE,
    memory=conversational_memory,
    early_stopping_method="generate",
    )

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
                    
                    if language == "Korean":
                        user_question = f"너는 이미지 속 시각적인 객체들을 한 줄로 설명해야돼. 웹사이트의 제목과 주변에 위치한 텍스트를 바탕으로 이미지의 시각적인 정보를 한 줄로 설명해. 이미지가 있는 웹사이트의 제목은 {title}이야. 그리고 이미지 주변에 위치한 텍스트는 {context}이야. 너는 최종적으로 답변을 한국어로 번역해야해."
                        response = agent.invoke(f"{user_question}, image path: {image_path}, translate_language: Korean")
                    elif language == "Japanese":
                        user_question = f"ウェブサイトのタイトルと周囲のテキストに基づいて、画像を 1 行で記述する。ウェブサイトのタイトルは{title}で、画像を囲むテキストは{context}です。君は最終的に答えを日本語に翻訳しなければならない。"
                        response = agent.invoke(f"{user_question}, image path: {image_path}, translate_language: Japanese")
                    elif language == "Chinese":
                        user_question = f"图像的文章标题为 {title}，图像的上下文为 {context}。最后您需要将答案翻译成中文。"
                        response = agent.invoke(f"{user_question}, image path: {image_path}, translate_language: Chinese")
                    elif language == "Spanish":
                        user_question = f"Describa la imagen en una línea basándose en el título del sitio web y el texto que la rodea. El título del sitio web es {title}, y el texto que rodea la imagen es {context}. Al final tendrás que traducir las respuestas al español."
                        response = agent.invoke(f"{user_question}, image path: {image_path}, translate_language: spanish")
                    else:
                        user_question = f"Describe the image in one line based on the title of the website and the surrounding text. The Website title is {title}, and the text surrounding the image is {context}."
                        response = agent.invoke(f"{user_question}, image path: {image_path}")

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
    
    data[image_name] = {"image_name": image_name, "response": response['output']}
    
    with open(response_file_path, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)
