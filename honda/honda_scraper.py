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

url = "https://www.honda2wheelersindia.com/dealer-locator"

# Store showroom data"
data = []

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
    time.sleep(2)  # Initial load wait
    
    return driver, wait

# Function to scrape the showrooms from particular city
def scrape_dealers(driver, wait, state, city):
    dealers = []
    page_source = driver.page_source
    soup = BeautifulSoup(page_source, "html.parser")
    
    container = soup.find("ol", class_="DealerLocator_dealerItems__BAUqC")
    showroom_list = container.find_all("li", class_="DealerLocator_dealer__sO4Kv")
    for showroom in showroom_list:

        name = showroom.find("p", class_="DealerLocator_dealer__Name__IFmch").text.strip()
        address = showroom.find("p", class_="DealerLocator_dealer__Address__TezsX").text.strip()
        dealers.append([name if name else "", address if address else "", city, state])
        print([name if name else "", address if address else "", city, state])
        
    return dealers
    
# Function to select state and city
def select_state_city(driver, wait):
    # Click to open the dropdown
    state_drop_down = driver.find_element(By.XPATH, '//*[@id="content"]/div/div/div/div/div/div/div/div/section/div/div/div/div/div/div[1]/div')
    state_drop_down.click()
    time.sleep(1)  # Wait for dropdown to open
 
    # Now get the container of options
    state_drop_down_options = driver.find_element(By.CLASS_NAME, 'css-1nmdiq5-menu')
    
    # Then find all option elements inside the menu
    options = state_drop_down_options.find_elements(By.CSS_SELECTOR, "div[class*='option']")

    state_names = [option.text for option in options]
    # state_names = state_names[:3]
    # print(state_names)
    
    for state in state_names:
        try:
            dropdown_inputs = driver.find_elements(By.XPATH, '//input[@role="combobox" and @aria-autocomplete="list"]')
    
            state_input = dropdown_inputs[0]
            city_input = dropdown_inputs[1]
            # Locate the input field using stable attributes
            # state_input = driver.find_element(By.XPATH, '//input[@role="combobox" and @aria-autocomplete="list"]')
            
            # Focus the field
            state_input.click()
            time.sleep(0.5)
        
            # Clear the input (CTRL+A then BACKSPACE)
            state_input.send_keys(Keys.CONTROL + "a")
            state_input.send_keys(Keys.BACKSPACE)
            time.sleep(0.5)
        
            # Type the new state name
            state_input.send_keys(state)
            time.sleep(1.5)  # Wait for the dropdown to show options
        
            # Move to the first option and select
            state_input.send_keys(Keys.ARROW_DOWN)
            state_input.send_keys(Keys.ENTER)
            time.sleep(1)  # Wait for selection to complete
            
            # Click to open the dropdown
            city_drop_down = driver.find_element(By.XPATH, '//*[@id="content"]/div/div/div/div/div/div/div/div/section/div/div/div/div/div/div[2]/div')
            city_drop_down.click()
            time.sleep(1)  # Wait for dropdown to open
         
            # Now get the container of options
            city_drop_down_options = driver.find_element(By.CLASS_NAME, 'css-1nmdiq5-menu')
            
            # Then find all option elements inside the menu
            city_options = city_drop_down_options.find_elements(By.CSS_SELECTOR, "div[class*='option']")
        
            city_names = [city_option.text for city_option in city_options]
            # print(city_names)
            for city in city_names:
                # Focus the field
                city_input.click()
                time.sleep(0.5)
            
                # Clear the input (CTRL+A then BACKSPACE)
                city_input.send_keys(Keys.CONTROL + "a")
                city_input.send_keys(Keys.BACKSPACE)
                time.sleep(0.5)
            
                # Type the new state name
                city_input.send_keys(city)
                time.sleep(1.5)  # Wait for the dropdown to show options
            
                # Move to the first option and select
                city_input.send_keys(Keys.ARROW_DOWN)
                city_input.send_keys(Keys.ENTER)
                time.sleep(1)  # Wait for selection to complete

                dealers = scrape_dealers(driver, wait, state, city)
                data.extend(dealers)
                
        except:
            pass


# Function to run the process step by step
def main():
    driver, wait = start_browser()
    select_state_city(driver, wait)
    driver.quit()
    
if __name__ == "__main__":
    main()
    
    df = pd.DataFrame(data, columns=["Showroom Name", "Address", "City", "State"]).drop_duplicates()
        
    # Save updated file
    filename = f"honda_showrooms_{today}.csv"
    df.to_csv(filename, index=False)
    print(f"Done! ✅ Updated DataFrame saved as {filename}")

