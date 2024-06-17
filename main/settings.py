from langchain.agents import initialize_agent
from langchain.chat_models import ChatOllama, ChatOpenAI
from langchain.callbacks import StreamingStdOutCallbackHandler
from langchain.chains.conversation.memory import ConversationBufferWindowMemory
from tools import ImageCaptionTool, ObjectDetectionTool
from transformers import BlipProcessor, BlipForConditionalGeneration, DetrImageProcessor, DetrForObjectDetection
from PIL import Image
import torch
# from langchain.schema import SystemMessage
import DEBUG
from langchain.prompts import SystemMessagePromptTemplate, ChatPromptTemplate

from langchain_core.messages.system import SystemMessage

def get_image_caption(image_path):
    """
    Generates a short caption for the provided image.

    Args:
        image_path (str): The path to the image file.

    Returns:
        str: A string representing the caption for the image.
    """
    image = Image.open(image_path).convert("RGB")

    model_name = "Salesforce/blip-image-captioning-large"

    # 나중에 cuda로 돌린다면, half로 돌리는 게 좋을듯
    # processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-large")
    # model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-large", torch_dtype=torch.float16).to("cuda")
    # device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    device = "cpu"

    processor = BlipProcessor.from_pretrained(model_name)
    model = BlipForConditionalGeneration.from_pretrained(model_name).to(device)

    inputs = processor(image, return_tensors="pt").to(device)
    output = model.generate(**inputs, max_new_tokens=20)

    caption = processor.decode(output[0], skip_special_tokens=True)

    return caption

def detect_objects(image_path):
    """
    Detects objects in the provided image.

    Args:
        image_path (str): The path to the image file.

    Returns:
        str: A string with all the detected objects. Each object as "[x1, x2, y1, y2, class_name, confindence_score]".
    """
    image = Image.open(image_path).convert("RGB")

    processor = DetrImageProcessor.from_pretrained("facebook/detr-resnet-50")
    model = DetrForObjectDetection.from_pretrained("facebook/detr-resnet-50")

    inputs = processor(images=image, return_tensors="pt")
    outputs = model(**inputs)

    target_sizes = torch.tensor([image.size[::-1]])
    results = processor.post_process_object_detection(outputs, target_sizes=target_sizes, threshold=0.9)[0]

    detections = ""
    for score, label, box in zip(results["scores"], results["labels"], results["boxes"]):
        detections += "[{}, {}, {}, {}]".format(int(box[0]), int(box[1]), int(box[2]), int(box[3]))
        detections += " {}".format(model.config.id2label[int(label)])
        detections += " {}\n".format(float(score))

    return detections


system_message_template = SystemMessagePromptTemplate.from_template("""
            You are an image descriptor for blind people.

            Explain the alternative text for the image.

            You only explain the core of the visual information in the image.
                                                                    """)

chat_template = ChatPromptTemplate.from_messages([system_message_template])
messages = chat_template.format_messages()

prompt = ChatPromptTemplate.from_messages(messages=messages)


if DEBUG.SELECT_LLM == 1:
    llm = ChatOpenAI(
        model="gpt-3.5-turbo",
        temperature=0.1,
        streaming=True,
        prompt = prompt,
        callbacks=[StreamingStdOutCallbackHandler()],
    )
elif DEBUG.SELECT_LLM == 2:
    llm = ChatOllama(
        model = "llama3:8b",    
        temperature=0.1,
        streaming=True,
        prompt = prompt,
        callbacks=[StreamingStdOutCallbackHandler()],
    )


conversational_memory = ConversationBufferWindowMemory(
    memory_key="chat_history",
    k=0,
    return_messages=True
)

tools = [ImageCaptionTool(), ObjectDetectionTool()]


agent = initialize_agent(
    agent="chat-conversational-react-description",
    tools=tools,
    llm=llm,
    max_iterations=5,
    verbose=DEBUG.VERBOSE,
    memory=conversational_memory,
    early_stopping_method="generate",
    # agent_kwargs={
    #     "system_message": SystemMessage(content="""
    #         You are an image descriptor for blind people.

    #         Explain the alternative text for the image.

    #         You only explain the core of the visual information in the image.            
    #         """
    #     ),
    # },
)