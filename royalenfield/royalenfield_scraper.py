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

prefs = {
  "profile.managed_default_content_settings.images": 2,
  "profile.default_content_setting_values.notifications": 2,
  "profile.default_content_setting_values.geolocation": 2
}
options.add_experimental_option("prefs", prefs)

###------------------ VARIABLES SECTION ------------------###

today = datetime.today().strftime("%d-%m-%Y")

url = "https://www.royalenfield.com/in/en/locate-us/dealers/"

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

# Function to scrape the showrooms from particular city
def scrape_dealers(driver, wait, city, state):
    dealers = []
    while True:
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, "html.parser")
        
        container = soup.find("div", id="dealer-list")
        showroom_list = container.find_all("div", class_="re-storelist-items")
        if showroom_list:
            for showroom in showroom_list:
                name_ele = showroom.find("div", class_="store-name").find("h2")
                name = name_ele.contents[0].strip() if name_ele.find("span") else name_ele.get_text(strip=True)

                addr_block = showroom.find('div', class_='re-storelist-addr')

                # Get all <p> tags that contain address lines
                p_tags = addr_block.find_all('p')
                address_lines = []
                
                # Extract and clean text from the first three <p> tags
                for i in range(3):
                    text = p_tags[i].get_text(separator='', strip=True).rstrip(',')
                    address_lines.append(text)
                
                # Join them together with comma
                address = ', '.join(address_lines)
                address = re.sub(r'\s+', ' ', address).strip()
                
                phone = addr_block.find('a', href=lambda x: x and x.startswith('tel:')).get_text(strip=True)
                email = addr_block.find('a', href=lambda x: x and x.startswith('mailto:')).get_text(strip=True)
                print([name, address, phone, email, city, state])
                dealers.append([name, address, phone, email, city, state])
                
            break
    # print(dealers)
    return dealers
    
# Function to select state and city
def select_state_city(driver, wait):
    while True:
        state_dropdown_ele = wait.until(EC.presence_of_element_located((By.ID, "stateSel")))
        state_dropdown = Select(state_dropdown_ele)

        if len(state_dropdown.options)>1:
            break

    for state in state_dropdown.options:
        state_value = state.get_attribute("value")
        if state_value == '':
            continue
        state_dropdown.select_by_value(state_value)

        while True:
            city_dropdown_ele = wait.until(EC.presence_of_element_located((By.ID, "districtSel")))
            city_dropdown = Select(city_dropdown_ele)
    
            if len(city_dropdown.options)>1:
                break
                
        for city in city_dropdown.options:
            city_value = city.get_attribute("value")
            if city_value == '':
                continue
            city_dropdown.select_by_value(city_value)

            dealers = scrape_dealers(driver, wait, city_value, state_value)
            data.extend(dealers)
                
                
# Function to run the process step by step
def main():
    driver, wait = start_browser()
    
    select_state_city(driver,wait)

    driver.quit()

if __name__ == "__main__":
    main()
    
    df = pd.DataFrame(data, columns=["Showroom Name", "Address", "Phone", "Email", "City", "State"]).drop_duplicates()
        
    # Save updated file
    filename = f"royalenfield_showrooms_{today}.csv"
    df.to_csv(filename, index=False)
    print(f"Done! ✅ Updated DataFrame saved as {filename}")
