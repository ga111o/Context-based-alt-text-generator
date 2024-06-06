import json
import numpy as np
from pycocotools.coco import COCO
import matplotlib.pyplot as plt
import skimage.io as io
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from tools import ImageCaptionTool, ObjectDetectionTool
from PIL import Image
import torch
from settings import agent

import os
import tempfile

with open('input.json', 'r') as f:
    data = json.load(f)

embeddings = OpenAIEmbeddings()
tools = [ImageCaptionTool(), ObjectDetectionTool()]
results = []
caption_wins = 0
llm_wins = 0

for image_key, image_data in data.items():
    texts = []
    image_captions = [image_data['context']]
    texts.extend(image_captions)
    
    out = FAISS.from_texts(texts, embeddings)

    img_path = image_data['image_path']
    caption_tool = ImageCaptionTool()
    caption = caption_tool._run(img_path)

    score_caption_model = out.similarity_search_with_score(caption)
    if len(score_caption_model) < len(image_captions):
        print(f"Warning: score_caption_model length ({len(score_caption_model)}) is less than the number of captions ({len(image_captions)})")

    caption_scores = [float(score[1]) for score in score_caption_model[:len(image_captions)]]
    avg_caption_score = sum(caption_scores) / len(caption_scores) if caption_scores else 0

    try:
        with Image.open(img_path) as img:
            if img.mode == "RGBA":
                img = img.convert("RGB")

            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
                img.save(tmp.name)
                image_path = tmp.name
                try:
                    user_question = f"Explain the image based on {image_captions}. DO NOT SAY ANYTHING ELSE."

                    print(f"user question: {image_captions}")
                    response = agent.run(f"{user_question}, image path: {image_path}")
                    
                except FileNotFoundError as e:
                    print(f"Can't open: {e}")
                    continue
    except FileNotFoundError as e:
        print(f"Can't open: {e}")
        continue

    score_llm_model = out.similarity_search_with_score(response)
    llm_scores = [float(score[1]) for score in score_llm_model[:len(image_captions)]]
    avg_llm_score = sum(llm_scores) / len(llm_scores) if llm_scores else 0

    if avg_caption_score < avg_llm_score:
        caption_wins += 1
    elif avg_llm_score < avg_caption_score:
        llm_wins += 1

    result = {
        "image_id": image_key,
        "caption_model": caption,
        "llm_model": response,
        "caption_model_scores": caption_scores,
        "llm_model_scores": llm_scores,
    }
    results.append(result)

final_results = {
    "caption_model_wins": caption_wins,
    "llm_model_wins": llm_wins,
    "results": results
}

with open('image_scores.json', 'w') as f:
    json.dump(final_results, f, indent=4)

print("\n\n\n====finished====\n")
