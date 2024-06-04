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


img_num = 2



dataDir='..'
dataType='val2017'
instances_annFile='{}/annotations/instances_{}.json'.format(dataDir,dataType)
coco = COCO(instances_annFile)

captions_annFile = '{}/annotations/captions_{}.json'.format(dataDir, dataType)
coco_caps = COCO(captions_annFile)


data = []
for _ in range(img_num):
    imgIds = coco.getImgIds()
    imgId = imgIds[np.random.randint(0, len(imgIds))]
    img = coco.loadImgs(imgId)[0]

    annIds = coco_caps.getAnnIds(imgIds=img['id'])
    anns = coco_caps.loadAnns(annIds)

    data.append({
        'image_id': img['id'],
        'image_name': img['file_name'],
        'image_path': f"{dataDir}/images/{dataType}/{img['file_name']}",
        'caption': [ann['caption'] for ann in anns]
    })

with open('image_captions.json', 'w') as f:
    json.dump(data, f)

##################################################

with open('image_captions.json', 'r') as f:
    data = json.load(f)

embeddings = OpenAIEmbeddings()
tools = [ImageCaptionTool(), ObjectDetectionTool()]
results = []

for image_data in data:
    texts = []
    image_captions = image_data['caption']
    texts.extend(image_captions)
    print(texts)
    out = FAISS.from_texts(texts, embeddings)

    img_path = image_data['image_path']
    caption_tool = ImageCaptionTool()
    caption = caption_tool._run(img_path)

    score_caption_model = out.similarity_search_with_score(caption)
    caption_scores = [{"caption": image_captions[i], "score": float(score_caption_model[i][1])} for i in range(len(image_captions)-1)]

    original_image_path = img_path
    try:
        with Image.open(original_image_path) as img:
            if img.mode == "RGBA":
                img = img.convert("RGB")

            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
                img.save(tmp.name)
                image_path = tmp.name

                try:
                    user_question = f"Describe the visual elements of the image based caption. DO NOT SAY ANYTHING ELSE"
                    response = agent.run(f"{user_question}, image path: {image_path}")
                    
                except FileNotFoundError as e:
                    print(f"Can't open: {e}")
    except FileNotFoundError as e:
        print(f"Can't open: {e}")
        continue

    score_llm_model = out.similarity_search_with_score(response)
    llm_scores = [{"caption": image_captions[i], "score": float(score_llm_model[i][1])} for i in range(len(image_captions)-1)]

    result = {
        "image_id": image_data['image_id'],
        "image_name": image_data['image_name'],
        "image_path": image_data['image_path'],
        "caption_model_output": caption,
        "caption_model_scores": caption_scores,
        "llm_model_output": response,
        "llm_model_scores": llm_scores
    }
    results.append(result)

with open('image_scores.json', 'w') as f:
    json.dump(results, f, indent=4)

print("\n\n\n====finished====\n")
