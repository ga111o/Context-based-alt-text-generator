import os
import requests
from bs4 import BeautifulSoup
from mimetypes import guess_extension
from urllib.parse import urljoin  

url = "http://127.0.0.1:8123/"  
output_folder = "./imgs"

if not os.path.exists(output_folder):
    os.makedirs(output_folder)

response = requests.get(url)
soup = BeautifulSoup(response.content, "html.parser")

img_tags = soup.find_all("img")

for i, img in enumerate(img_tags):
    if not img.has_attr('alt'):
        img_url = img.get("src")
        if img_url:
            full_img_url = urljoin(url, img_url)  
            img_response = requests.get(full_img_url, stream=True)
            img_content_type = img_response.headers['Content-Type']
            img_extension = guess_extension(img_content_type)
            img_name = f"{i}{img_extension}"
            img_path = os.path.join(output_folder, img_name)
            with open(img_path, "wb") as img_file:
                for chunk in img_response.iter_content(chunk_size=8192):
                    img_file.write(chunk)
            print(f"donwload: {img_path}")

print("done!")
