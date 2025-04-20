###------------------ IMPORT SECTION ------------------###

# Import required libraries
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import UnexpectedAlertPresentException, TimeoutException
from selenium.webdriver.common.alert import Alert

import pandas as pd
import time
import csv
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re

###------------------ CONFIGURATION SECTION ------------------###

# Setup Chrome WebDriver - Configure Selenium to use Chrome
options = Options()
options.add_argument("--headless=new")  # Correct syntax for headless
options.add_argument("--disable-popup-blocking")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--start-maximized")
options.add_argument("user-agent=Mozilla/5.0")

# Optional: Disable image loading (better done via prefs)
# prefs = {"profile.managed_default_content_settings.images": 2}
# options.add_experimental_option("prefs", prefs)

# prefs = {
#   "profile.managed_default_content_settings.images": 2,
#   "profile.default_content_setting_values.notifications": 2,
#   "profile.default_content_setting_values.geolocation": 2
# }
# options.add_experimental_option("prefs", prefs)

###------------------ VARIABLES SECTION ------------------###

today = datetime.today().strftime("%d-%m-%Y")

url = "https://dealers.heromotocorp.com/"

# Store showroom data"
data = []
state_cities = {}

# Constants
MAX_RETRIES = 2  # Number of retries per pincode
RESTART_BROWSER_AFTER = 10  # Restart Chrome every N pincodes
WAIT_TIME = 10  # Increased explicit wait time
DATA_SAVE_INTERVAL = 10  # Save every N pincodes

###------------------ PROCESS SECTION ------------------###

# Funtion to start a browser
def start_browser():
    """Starts a new browser session."""
    driver = webdriver.Chrome(service=Service(), options=options)
    driver.maximize_window()
    wait = WebDriverWait(driver, WAIT_TIME, poll_frequency=0.5)

    driver.get(url)
    time.sleep(5)  # Initial load wait
    
    return driver, wait

# Function to select state and city
def select_state_city(driver, wait):
    while True:
        # Wait until the element is present
        target_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "/html/body/section[2]/div[2]"))
        )
        
        # Scroll to the element using JavaScript
        driver.execute_script("arguments[0].scrollIntoView({ behavior: 'smooth', block: 'center' });", target_element)
      
        # Get the Select object from the state dropdown
        state_dropdown_ele = wait.until(EC.presence_of_element_located((By.ID, "OutletState")))
        state_dropdown = Select(state_dropdown_ele)

        if len(state_dropdown.options)>1:
            break
            
    for state in state_dropdown.options:
        state_value = state.get_attribute("value")
        if state_value == '':
            continue
        state_dropdown.select_by_value(state_value)
        print(state.text)

        while True:
            # Get the Select object from the state dropdown
            city_dropdown_ele = wait.until(EC.presence_of_element_located((By.ID, "OutletCity")))
            city_dropdown = Select(city_dropdown_ele)
    
            if len(city_dropdown.options)>1:
                break
                
        for city in city_dropdown.options:
            city_value = city.get_attribute("value")
            if city_value == '':
                continue
            city_dropdown.select_by_value(city_value)
            print(city.text)
        
    
# Function to run the process step by step
def main():
    driver, wait = start_browser()
    
    select_state_city(driver,wait)

    driver.quit()
    
if __name__ == "__main__":
    main()
