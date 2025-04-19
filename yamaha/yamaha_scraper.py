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

url = "https://www.yamaha-motor-india.com/dealer-network.html"

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
    time.sleep(2)  # Initial load wait
    
    return driver, wait

# Function to scrape the showrooms from particular city
def scrape_dealers(driver, wait, state, city):
    dealers = []
    page_source = driver.page_source
    soup = BeautifulSoup(page_source, "html.parser")
    
    container = soup.find("div", id="all_search_result")
    showroom_list = soup.find_all("div", class_="slick-list draggable")
    for showroom in showroom_list:
        showroom_details = showroom.find("div", class_="dealers-info-content")
        name = showroom_details.find("h4").text.strip()
        
        address_icon = showroom_details.find("i", class_="fa-regular fa-map")
        phone_icon = showroom_details.find("i", class_="fa-solid fa-mobile-screen")
        
        address = address_icon.next_sibling.text.replace('"','').strip()
        phone = phone_icon.next_sibling.text.replace('"','').strip()

        dealers.append([name if name else "", address if address else "", phone if phone else "", city, state])
        print([name if name else "", address if address else "", phone if phone else "", city, state])
        
    return dealers
    
# Function to select state and city
def select_state_city(driver, wait):
  type_dropdown = Select(wait.until(EC.presence_of_element_located((By.ID, "type"))))
  type_dropdown.select_by_value("sales")
  # Get the Select object from the state dropdown
  state_dropdown = Select(wait.until(EC.presence_of_element_located((By.ID, "state"))))
  for index in range(len(state_dropdown.options)):
    retry_count = 0
    while retry_count < MAX_RETRIES:
      try:
        # Re-fetch the dropdown and its options on every iteration
        state_dropdown = Select(wait.until(EC.presence_of_element_located((By.ID, "state"))))
        state_option = state_dropdown.options[index]
        print("1")
        state_value = state_option.text
        print("4")
        state = state_option.get_attribute("value")
        if not state:
            continue
        if state_value == "-- State --":
            break
        print("Selecting state:", state_value)
        state_dropdown.select_by_value(state)

        # wait or do actions here (like triggering city loading, etc.)
        time.sleep(2)  # Or use a better WebDriverWait

        # Get the Select object from the city dropdown
        city_dropdown = Select(wait.until(EC.presence_of_element_located((By.ID, "city"))))
        for index in range(len(city_dropdown.options)):
          retry_count_city = 0
          while retry_count_city < MAX_RETRIES:
            try:
              # Re-fetch the dropdown and its options on every iteration
              city_dropdown = Select(wait.until(EC.presence_of_element_located((By.ID, "city"))))
      
              city_option = city_dropdown.options[index]
              city_value = city_option.text
      
              city = city_option.get_attribute("value")
      
              if not city:
                  continue
              print("Selecting city:", city_value)
              city_dropdown.select_by_value(city)
      
              # wait or do actions here
              time.sleep(3)  # Or use a better WebDriverWait
  
              dealers = scrape_dealers(driver, wait, state_value, city_value)
              data.extend(dealers)
              break
            except:
              retry_count_city += 1
              if retry_count_city == MAX_RETRIES:
                break
      except:
        retry_count += 1
        if retry_count == MAX_RETRIES:
          break
    
# Function to run the process step by step
def main():
    driver, wait = start_browser()
    select_state_city(driver, wait)
    driver.quit()

if __name__ == "__main__":
    main()
    df = pd.DataFrame(data, columns=["Showroom Name", "Address", "Phone", "City", "State"]).drop_duplicates()
        
    # Save updated file
    filename = f"yamaha_showrooms_{today}.csv"
    df.to_csv(filename, index=False)
    print(f"Done! ✅ Updated DataFrame saved as {filename}")
