from selenium.webdriver.firefox.service import Service
from selenium import webdriver

# cpu: 1
# cuda: 2 
# auto detected: 3
SELECT_DEVICE = 3

# 1: gpt3.5-turbo
# 2: llama8:3b
SELECT_LLM = 1

# DRIVER_PATH = "./gecko/geckodriver"

# options = webdriver.FirefoxOptions()
# options.add_argument("--disable-dev-shm-usage")
# options.add_argument("user-agent={Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36}")
# # options.add_argument('--headless')
# service = Service(executable_path=DRIVER_PATH)
# DRIVER = webdriver.Firefox(service=service, options=options)

options_chrome = webdriver.ChromeOptions()
options_chrome.add_argument("--disable-dev-shm-usage")
options_chrome.add_argument("user-agent={Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36}")
# options_chrome.add_argument('--headless')
DRIVER_CHROME = webdriver.Chrome(options=options_chrome)

VERBOSE = False

LOGGING = True

PRINT_LOG_BOOLEN = True # true or false
CREATE_FILE_FOR_CHECK_LINE_BOOLEN = False # true or false

DELETE_DATABASE = False
