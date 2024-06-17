from langchain.agents import initialize_agent
from langchain.chat_models import ChatOllama, ChatOpenAI
from langchain.callbacks import StreamingStdOutCallbackHandler
from langchain.chains.conversation.memory import ConversationBufferWindowMemory
from tools import ImageCaptionTool, ObjectDetectionTool
from langchain.prompts import SystemMessagePromptTemplate, ChatPromptTemplate
import DEBUG

system_message_template = SystemMessagePromptTemplate.from_template("""
            You are an image descriptor for blind people.

            you must describe the image based on article's title and context
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
)