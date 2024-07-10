from selenium.webdriver.firefox.service import Service
from selenium import webdriver

# cpu: 1
# cuda: 2 
# auto detected: 3
SELECT_DEVICE = 3

# 1: gpt3.5-turbo
# 2: llama8:3b
SELECT_LLM = 1

DRIVER_PATH = "./gecko/geckodriver"

options = webdriver.FirefoxOptions()
options.add_argument('--headless')
service = Service(executable_path=DRIVER_PATH)
DRIVER = webdriver.Firefox(service=service, options=options)

VERBOSE = True

LOGGING = True

PRINT_LOG_BOOLEN = True # true or false
CREATE_FILE_FOR_CHECK_LINE_BOOLEN = False # true or false

DELETE_DATABASE = True
