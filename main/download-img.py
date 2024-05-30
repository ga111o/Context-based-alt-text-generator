from selenium import webdriver
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

if DEBUG.PRINT_LOG_BOOLEN:
    print("========= in the download-img.py ==============")

gecko_driver_path = "./gecko/geckodriver"

options = webdriver.FirefoxOptions()
options.add_argument('--headless')

service = Service(executable_path=gecko_driver_path)
driver = webdriver.Firefox(service=service, options=options)

if len(sys.argv) > 4:
    session = sys.argv[1]
    url = sys.argv[2]
    language = sys.argv[3]
    title = sys.argv[4]

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
        alt_text = image.get_attribute('alt')
        # if alt_text:
        #     if DEBUG.PRINT_LOG_BOOLEN:
        #         print(f"===============skipping img with alt: {alt_text}")
            # continue  // alt 있어도 일단 다운로드 하도록

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
                    print(f"===============skipping SVG img: {image_original_name}")
                continue
            
            MAX_FILENAME_LENGTH = 255
            if len(image_original_name) > MAX_FILENAME_LENGTH:
                if DEBUG.PRINT_LOG_BOOLEN:
                    print(f"=============== name is too long.... skipping {image_original_name}")
                continue
                
            image_file = os.path.join(img_folder, image_original_name)
            
            with open(image_file, 'wb') as file:
                file.write(image_content)
                
            try:
                with Image.open(image_file) as img:
                    img.verify()  ## i supper luv verify().... 와 정상적인 이미지만 어케 골라내지 했는데 했는데 이게 되네
                with Image.open(image_file) as img:
                    if img.mode == 'RGBA':
                        img = img.convert('RGB')
                        img.save(image_file, 'JPEG')
                    if img.width < 100 or img.height < 100:
                        if DEBUG.PRINT_LOG_BOOLEN:
                            print(f"===============small img({img.width}x{img.height}): {image_original_name} ")
                        os.remove(image_file)
                        continue
                    
            except (UnidentifiedImageError, OSError) as e:
                if DEBUG.PRINT_LOG_BOOLEN:
                    print(f"===============skipping invalid img: {image_original_name} error: {e}")
                os.remove(image_file)
                continue

            parent_element = image.find_element(By.XPATH, '..')
            context = parent_element.text

            response_data[image_original_name] = {
                "image_path": image_file,
                "context": context,
                "language": language,
                "title": title
            }
            if DEBUG.PRINT_LOG_BOOLEN:
                print(f"download {image_file}")
                
    if DEBUG.PRINT_LOG_BOOLEN:
        print(f"===============session: {session} ==================")
        print(f"===============download: {len(images)} imgs ==================")

finally:
    driver.quit()

with open(os.path.join(response_folder, "input.json"), "w", encoding="utf-8") as json_file:
    json.dump(response_data, json_file, indent=4, ensure_ascii=False)
