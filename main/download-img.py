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
from selenium.webdriver.firefox.service import Service
from selenium import webdriver

import time

DRIVER_PATH = "./gecko/geckodriver"

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

img_folder = os.path.join(os.path.dirname(__file__), "source",session,"imgs")
response_folder = f"./source/{session}/responses"
db_folder = "./database"

if not os.path.exists(img_folder):
    os.makedirs(img_folder)
if not os.path.exists(response_folder):
    os.makedirs(response_folder)
if not os.path.exists(db_folder):
    os.makedirs(db_folder)

options = webdriver.FirefoxOptions()
options.add_argument("--disable-dev-shm-usage")
options.add_argument("user-agent={Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36}")
options.add_argument('--headless')
options.set_preference("browser.download.dir", img_folder)
options.set_preference("browser.download.folderList", 2)
options.set_preference("browser.helperApps.neverAsk.saveToDisk", "image/jpeg,image/webp,image/png,image/gif")

service = Service(executable_path=DRIVER_PATH)
driver = webdriver.Firefox(service=service, options=options)

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
    lmm_output TEXT,
    object_output TEXT,
    origianl_alt TEXT
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
    
    for img_element in images:
        try:
            src = img_element.get_attribute("src")
            alt_text = img_element.get_attribute('alt')
            
            img_extension = os.path.splitext(os.path.basename(src))[1]
            image_full_path = os.path.join(img_folder, os.path.basename(src))
            image_original_name = f"{os.path.splitext(os.path.basename(src))[0]}{img_extension}"

            driver.execute_script(f"var xhr = new XMLHttpRequest(); xhr.open('GET', '{src}', true); xhr.responseType = 'blob'; xhr.onload = function(e) {{ if (this.status == 200) {{ var blob = this.response; var img = document.createElement('img'); img.src = window.URL.createObjectURL(blob); document.body.appendChild(img); var a = document.createElement('a'); a.href = img.src; a.download = '{image_original_name}'; document.body.appendChild(a); a.click(); }} }}; xhr.send();")
            
            relative_path = os.path.relpath(image_full_path, "/home/ga111o/document/MarkDown/kwu-idea-lab/projects/add-alt-using-llm/main")
            
            image_file = os.path.abspath(os.path.join(".", relative_path))

            time.sleep(0.3)

            img_hash = get_image_hash(image_full_path)

            parent_element = img_element.find_element(By.XPATH, '..')
            context = parent_element.text

            response_data[image_original_name] = {
                "image_path": image_file,
                "context": context,
                "language": language,
                "title": title,
                "original_url": src,
                "hash": img_hash,
                "original_alt": alt_text
            }

            cursor.execute("SELECT COUNT(*) FROM images WHERE hash = ?", (img_hash,))
            exists = cursor.fetchone()[0]

            if exists == 0:
                cursor.execute("""
                    INSERT INTO images (image_name, original_url, img_path, context, language, title, hash, origianl_alt)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (image_original_name, src, image_file, context, language, title, img_hash, alt_text))
                conn.commit()

                if DEBUG.PRINT_LOG_BOOLEN:
                    print(f" | {session} |---- download {image_original_name}")
                    print(f" | {session} |------ relative_path: {relative_path}")
                    print(f" | {session} |------ img_hash: {img_hash}")
                    print(f" | {session} |------ inserted database {image_original_name}")
            else:
                if DEBUG.PRINT_LOG_BOOLEN:
                    print(f" | {session} |---- already exists {image_original_name}")
        
        except Exception as e:
            if DEBUG.PRINT_LOG_BOOLEN:
                print(f" | {session} | ---- skipping {e}")

except Exception as e:
    if DEBUG.PRINT_LOG_BOOLEN:
        print(f" | {session} | ---- error {url}, {e}")

finally:
    driver.quit()

with open(os.path.join(response_folder, "input.json"), "w", encoding="utf-8") as json_file:
    json.dump(response_data, json_file, indent=4, ensure_ascii=False)

conn.close()