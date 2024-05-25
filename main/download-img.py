from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
import requests
import os
import sys
import json
from urllib.parse import urlparse, unquote
import base64
import DEBUG

if DEBUG.PRINT_LOG_BOOLEN:
    print("========= in the download-img.py ==============")

gecko_driver_path = "./gecko/geckodriver"

options = webdriver.FirefoxOptions()
options.add_argument('--headless')

service = Service(executable_path=gecko_driver_path)
driver = webdriver.Firefox(service=service, options=options)

if len(sys.argv) > 3:
    session = sys.argv[1]
    url = sys.argv[2]
    language = sys.argv[3]

img_folder = f"./source/{session}/imgs"
response_folder = f"./source/{session}/responses"

if not os.path.exists(img_folder):
    os.makedirs(img_folder)
if not os.path.exists(response_folder):
    os.makedirs(response_folder)

response_data = {}

try:
    driver.get(url)
    images = driver.find_elements(By.TAG_NAME, 'img')

    for i, image in enumerate(images):
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
            
            MAX_FILENAME_LENGTH = 255
            if len(image_original_name) > MAX_FILENAME_LENGTH:
                if DEBUG.PRINT_LOG_BOOLEN:
                    print(f"name is too long.... skipping {image_original_name}")
                continue
                
            image_file = os.path.join(img_folder, image_original_name)
            
            with open(image_file, 'wb') as file:
                file.write(image_content)
                
            parent_element = image.find_element(By.XPATH, '..')
            context = parent_element.text

            response_data[image_original_name] = {
                "image_path": image_file,
                "context": context,
                "language": language
            }
            if DEBUG.PRINT_LOG_BOOLEN:
                print(f"=============download {image_file} ================")
                
    if DEBUG.PRINT_LOG_BOOLEN:
        print(f"===============session: {session} ==================")
        print(f"===============download: {len(images)} imgs ==================")

finally:
    driver.quit()

with open(os.path.join(response_folder, "input.json"), "w", encoding="utf-8") as json_file:
    json.dump(response_data, json_file, indent=4, ensure_ascii=False)
