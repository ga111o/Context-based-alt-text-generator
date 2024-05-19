from celery_app import app
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import os
import json
import subprocess

@app.task
def get_url_n_img(url, session, language):
    img_folder = f"./source/{session}/imgs"
    response_folder = f"./source/{session}/responses"

    if not os.path.exists(img_folder):
        os.makedirs(img_folder)

    if not os.path.exists(response_folder):
        os.makedirs(response_folder)

    response_data = {}

    try:
        response = requests.get(url)
        if response.status_code != 200:
            print("========== ERROR: response.status_code != 200")
    except ConnectionError:
        print("========== ERROR: connection error 2")

    soup = BeautifulSoup(response.content, "html.parser")
    img_tags = soup.find_all("img")

    downloaded_files = set()

    for img in img_tags:
        if not img.has_attr("alt"):
            img_url = img.get("src")
            if img_url:
                full_img_url = urljoin(url, img_url)
                img_name = os.path.basename(urlparse(full_img_url).path) 

                downloaded_files.add(img_name)

                try:
                    img_response = requests.get(full_img_url, stream=True)
                    if img_response.status_code == 200:
                        img_path = os.path.join(img_folder, img_name)
                        with open(img_path, "wb") as img_file:
                            for chunk in img_response.iter_content(chunk_size=8192):
                                img_file.write(chunk)
                        print(f"download: {img_path}")

                        context = img.parent.get_text(strip=True)
                        response_data[img_name] = {
                            "image_path": img_path,
                            "context": context,
                            "language": language
                        }
                except ConnectionError:
                    print(f"failed download image: {img_url}")

    with open(f"{response_folder}/input.json", "w", encoding="utf-8") as json_file:
        json.dump(response_data, json_file, indent=4, ensure_ascii=False)

    subprocess.call(["python", "add-alt.py", session])
