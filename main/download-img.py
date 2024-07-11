from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
import requests
import os
import sys
import json
from urllib.parse import urlparse, unquote
import base64
from PIL import Image, UnidentifiedImageError
import DEBUG
import sqlite3
import hashlib


driver = DEBUG.DRIVER

if len(sys.argv) > 4:
    session = sys.argv[1]
    url = sys.argv[2]
    language = sys.argv[3]
    title = sys.argv[4]

    if DEBUG.PRINT_LOG_BOOLEN:
        print(f" | {session} |-- in the download-img.py")

        print(f" | {session} |---- sys.argv[1]", sys.argv[1])
        print(f" | {session} |---- sys.argv[2]", sys.argv[2])
        print(f" | {session} |---- sys.argv[3]", sys.argv[3])
        print(f" | {session} |---- sys.argv[4]", sys.argv[4])

img_folder = f"./source/{session}/imgs"
response_folder = f"./source/{session}/responses"
db_folder = "./database"

if not os.path.exists(img_folder):
    os.makedirs(img_folder)
if not os.path.exists(response_folder):
    os.makedirs(response_folder)
if not os.path.exists(db_folder):
    os.makedirs(db_folder)

db_path = os.path.join(db_folder, "images.db")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS images (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    image_name TEXT,
    original_url TEXT,
    img_path TEXT,
    context TEXT,
    language TEXT,
    title TEXT,
    hash TEXT,
    caption_output TEXT,
    llm_output TEXT,
    lmm_output TEXT
)
""")
conn.commit()

def get_image_hash(image_path):
    hasher = hashlib.sha256()
    with open(image_path, 'rb') as img_file:
        buf = img_file.read()
        hasher.update(buf)
    return hasher.hexdigest()

response_data = {}

try:
    driver.get(url)
    images = driver.find_elements(By.TAG_NAME, 'img')

    for i, image in enumerate(images):
        alt_text = image.get_attribute('alt')
        src = image.get_attribute('src')

        if src:
            if src.startswith('data:image'):
                base64_encoded_data = src.split(',')[1]
                image_content = base64.b64decode(base64_encoded_data)
                image_original_name = f"image_{i}.png"
            else:
                image_content = requests.get(src).content
                parsed_url = urlparse(src)
                image_original_name = os.path.basename(unquote(parsed_url.path))

            if image_original_name.endswith('.svg'):
                if DEBUG.PRINT_LOG_BOOLEN:
                    print(f" | {session} |---- skipping SVG img")
                continue

            MAX_FILENAME_LENGTH = 255
            if len(image_original_name) > MAX_FILENAME_LENGTH:
                if DEBUG.PRINT_LOG_BOOLEN:
                    print(f" | {session} |---- skipping too long name img")
                continue

            image_file = os.path.join(img_folder, image_original_name)

            with open(image_file, 'wb') as file:
                file.write(image_content)

            try:
                with Image.open(image_file) as img:
                    img.verify()
                with Image.open(image_file) as img:
                    if img.mode == 'RGBA':
                        img = img.convert('RGB')
                        img.save(image_file, 'JPEG')
                    if img.width < 100 or img.height < 100:
                        if DEBUG.PRINT_LOG_BOOLEN:
                            print(f" | {session} |---- skipping too small img({img.width}x{img.height})")
                        os.remove(image_file)
                        continue

            except (UnidentifiedImageError, OSError) as e:
                if DEBUG.PRINT_LOG_BOOLEN:
                    print(f" | {session} |---- skipping invalid img {e}")
                os.remove(image_file)
                continue

            with open(image_file, 'rb') as img_file:
                img_hash = get_image_hash(image_file)

            parent_element = image.find_element(By.XPATH, '..')
            context = parent_element.text

            response_data[image_original_name] = {
                "image_path": image_file,
                "context": context,
                "language": language,
                "title": title,
                "original_url": src,
                "hash": img_hash
            }

            cursor.execute("SELECT COUNT(*) FROM images WHERE hash = ?", (img_hash,))
            exists = cursor.fetchone()[0]

            if exists == 0:
                cursor.execute("""
                    INSERT INTO images (image_name, original_url, img_path, context, language, title, hash)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (image_original_name, src, image_file, context, language, title, img_hash))
                conn.commit()

                if DEBUG.PRINT_LOG_BOOLEN:
                    print(f" | {session} |---- inserted database {image_original_name}")
                    print(f" | {session} |---- download {image_file}")
            else:
                if DEBUG.PRINT_LOG_BOOLEN:
                    print(f" | {session} |---- already exists {image_original_name}")


finally:
    driver.quit()

with open(os.path.join(response_folder, "input.json"), "w", encoding="utf-8") as json_file:
    json.dump(response_data, json_file, indent=4, ensure_ascii=False)

conn.close()