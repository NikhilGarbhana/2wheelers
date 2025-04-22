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

# Function to scrape the showrooms from particular city
def scrape_dealers(driver, wait, city, state):
    dealers = []
    while True:
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, "html.parser")
        
        container = soup.find("div", class_="outlet-list")
        showroom_list = container.find_all("div", class_="store-info-box")
        if showroom_list:
            for showroom in showroom_list:
                name = showroom.find("li", class_="outlet-name").text.strip()
                address = showroom.find("li", class_="outlet-address").text.strip()
                phone = showroom.find("li", class_="outlet-phone").text.strip()
                print([name if name else "", address if address else "", phone if phone else "", city, state])
                dealers.append([name if name else "", address if address else "", phone if phone else "", city, state])
                
        # Check for "Next" button
        try:
            next_button = WebDriverWait(driver, 3).until(EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Next')]")))

            # Check if it's disabled or not present
            if 'disabled' in next_button.get_attribute("class").lower():
                break

            # Scroll to and click the next button
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_button)
            time.sleep(1)
            next_button.click()
            time.sleep(2)  # Give it time to load new content

        except Exception as e:
            print("No more pages or error while clicking next")
            break
    return dealers
    
# Function to select state and city
def select_state_city(driver, wait):
    while True:
        # try:
        # Wait until the element is present
        # target_element = WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, "/html/body/section[2]/div[2]")))
        target_element = driver.find_element(By.XPATH, "/html/body/section[2]/div[2]")
        
        # Scroll to the element using JavaScript
        driver.execute_script("arguments[0].scrollIntoView({ behavior: 'smooth', block: 'center' });", target_element)
        
        # Get the Select object from the state dropdown
        state_dropdown_ele = wait.until(EC.presence_of_element_located((By.ID, "OutletState")))
        state_dropdown = Select(state_dropdown_ele)

        if len(state_dropdown.options)>1:
            break
        # except:
        #     driver.refresh()
        #     time.sleep(10)
    
    # for state in state_dropdown.options):
    for index in range(len(state_dropdown.options)):
        
        # Wait until the element is present
        target_element = WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, "/html/body/section[2]/div[2]")))
        
        # Scroll to the element using JavaScript
        driver.execute_script("arguments[0].scrollIntoView({ behavior: 'smooth', block: 'center' });", target_element)

        # Get the Select object from the state dropdown
        state_dropdown_ele = wait.until(EC.presence_of_element_located((By.ID, "OutletState")))
        state_dropdown = Select(state_dropdown_ele)
        
        state_value = state_dropdown.options[index].get_attribute("value")
        if state_value == '':
            continue
        state_dropdown.select_by_value(state_value)
        state_name = state_dropdown.options[index].text
        print(state_name)

        while True:
            
            # Get the Select object from the state dropdown
            city_dropdown_ele = wait.until(EC.presence_of_element_located((By.ID, "OutletCity")))
            city_dropdown = Select(city_dropdown_ele)
    
            if len(city_dropdown.options)>1:
                break
                
        # for city in city_dropdown.options:
        for index in range(len(city_dropdown.options)):
            
            # Wait until the element is present
            target_element = WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, "/html/body/section[2]/div[2]")))
            
            # Scroll to the element using JavaScript
            driver.execute_script("arguments[0].scrollIntoView({ behavior: 'smooth', block: 'center' });", target_element)

            # Get the Select object from the state dropdown
            city_dropdown_ele = wait.until(EC.presence_of_element_located((By.ID, "OutletCity")))
            city_dropdown = Select(city_dropdown_ele)
            
            city_value = city_dropdown.options[index].get_attribute("value")
            if city_value == '':
                continue
            city_dropdown.select_by_value(city_value)
            city_name = city_dropdown.options[index].text
            print(city_name)
            # driver.execute_script("window.scrollTo(0,500);")
            submit = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="OutletStoreLocatorSearchForm"]/div/div[2]/div[2]/input')))
            submit.click()
            time.sleep(3)
            
            # Wait until the element is present
            
            # target_container = WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, "/html/body/section[3]/div")))
            
            # # Scroll to the element using JavaScript
            # driver.execute_script("arguments[0].scrollIntoView({ behavior: 'smooth', block: 'center' });", target_container)
            
            dealers = scrape_dealers(driver, wait, city_name, state_name)
            data.extend(dealers)
        
    
# Function to run the process step by step
def main():
    driver, wait = start_browser()
    
    select_state_city(driver,wait)

    driver.quit()
    
if __name__ == "__main__":
    main()
    
    df = pd.DataFrame(data, columns=["Showroom Name", "Address", "Phone", "City", "State"]).drop_duplicates()
        
    # Save updated file
    filename = f"hero_showrooms_{today}.csv"
    df.to_csv(filename, index=False)
    print(f"Done! ✅ Updated DataFrame saved as {filename}")
