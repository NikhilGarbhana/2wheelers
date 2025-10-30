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
import numpy as np
import time
import csv
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re
import json
import os
import tempfile
import uuid

###------------------ CONFIGURATION SECTION ------------------###


# Setup Chrome WebDriver - Configure Selenium to use Chrome
options = Options()
# options.add_argument("--headless=new")  # Correct syntax for headless
options.add_argument("--disable-popup-blocking")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--start-maximized")
options.add_argument("user-agent=Mozilla/5.0")

# # Optional: Disable image loading (better done via prefs)
# prefs = {"profile.managed_default_content_settings.images": 2}
# options.add_experimental_option("prefs", prefs)

###------------------ VARIABLES SECTION ------------------###

data = []

# Constants
today = datetime.today().strftime("%d-%m-%Y")
url = "https://www.olaelectric.com/experience-centre-info"
MAX_RETRIES = 3  # Number of retries per pincode
RESTART_BROWSER_AFTER = 10  # Restart Browser every N cities
WAIT_TIME = 10  # Increased explicit wait time
DATA_SAVE_INTERVAL = 30  # Save every N cities
cities_list = []
cities = [] # Save cities list here

# List of Indian states
states = [
    "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh", "Goa",
    "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand", "Karnataka", "Kerala",
    "Madhya Pradesh", "Maharashtra", "Manipur", "Meghalaya", "Mizoram", "Nagaland",
    "Odisha", "Punjab", "Rajasthan", "Sikkim", "Tamil Nadu", "Telangana", "Tripura",
    "Uttar Pradesh", "Uttarakhand", "West Bengal", "Delhi", "Jammu and Kashmir",
    "Ladakh", "Puducherry", "Chandigarh", "Andaman and Nicobar Islands",
    "Dadra and Nagar Haveli and Daman and Diu", "Lakshadweep"
]

nominatim_cache = {}

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
def scrape_dealers(driver, wait, city):
    city_dropdown = wait.until(EC.visibility_of_element_located((By.XPATH, '//*[@id="your-city-is-here"]')))
    city_dropdown.click()
    time.sleep(2)

    search_box = driver.find_element(By.XPATH, '//*[@id="search_the_center"]')
    search_box.send_keys(city.text)

    x = '//*[@id="' + city.text.lower() + '"]'
    city_value = wait.until(EC.visibility_of_element_located((By.XPATH, x)))
    # driver.execute_script("arguments[0].scrollIntoView(true);", city_dropdown)
    driver.execute_script("window.scrollTo(0,200);")
    time.sleep(1)
    city_value.click()
    time.sleep(2)

    print(f"Scraping data for city - {city.text}...")
    page_source = driver.page_source
    soup = BeautifulSoup(page_source, "html.parser")
    showroom_list = soup.find(class_="slick-track")
    showrooms = showroom_list.find_all("div")

    dealers = []
    for showroom in showrooms:
        try:
            name = showroom.find("div", class_="experince-center-name").text.strip()
        except:
            name = ""
        try:
            address = showroom.find("div", class_="experince-center-address").text.strip()
        except:
            address = ""

        dealers.append([name, address, city.text])
    
    return dealers

def extract_state(address):
    for state in states:
        if re.search(rf'\b{re.escape(state)}\b', address, re.IGNORECASE):
            return state
    return "Unknown"

def extract_pincode(address):
    match = re.search(r'\b\d{6}\b', address)
    return match.group(0) if match else None

def get_state_from_nominatim_cached(address):
    if address in nominatim_cache:
        return nominatim_cache[address]
    
    url = 'https://nominatim.openstreetmap.org/search'
    params = {
        'q': address,
        'format': 'json',
        'addressdetails': 1
    }
    headers = {'User-Agent': 'YourApp/1.0'}

    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data and data[0]['address'].get('country_code', 'Unknown')=='in':
            state = data[0]['address'].get('state', 'Unknown')
        else:
            state = 'Unknown'
    except requests.RequestException as e:
        print(f"Error fetching state for address: {address} | Error: {e}")
        state = 'Unknown'

    # Save to cache
    nominatim_cache[address] = state
    return state
    
# Function to run the process step by step
def main():
    driver, wait = start_browser()
    # time.sleep(10)
    
    page_source = driver.page_source
    soup = BeautifulSoup(page_source, "html.parser")
    container = soup.find("ul", id="all_cityname")
    city_list = container.find_all("li")
    
    for city in city_list:
        # print(city.text)
        retry_count = 0
        # scrape_dealers(driver, wait, city)
        while retry_count < MAX_RETRIES:
            try:
                dealers = scrape_dealers(driver, wait, city)
                data.extend(dealers)
                break
            except Exception as e:
                retry_count += 1
                # print(e)
                if retry_count == MAX_RETRIES:
                    break
                if "interested-pop-up" in str(e):
                    close_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@class="interested-close close-btn"]')))
                    close_button.click()
                    # driver.execute_script("document.querySelector('interested-close close-btn').style.display = 'none';")
                if "mgz-element-inner" in str(e):
                    close_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@class="subscribe_popup_close"]')))
                    close_button.click()
        
    driver.quit()
    
if __name__ == "__main__":
    main()

    df = pd.DataFrame(data, columns=["Showroom Name", "Address", "City"]).drop_duplicates()
    # Drop empty showroom names
    df['Showroom Name'] = df['Showroom Name'].replace('', np.nan)
    df = df.dropna(subset=['Showroom Name'])
    
    # Extract state from address using regex
    df['State'] = df['Address'].apply(extract_state)
    
    # Step 1: City to state mapping from rows where state is known
    city_state_map = (
        df[df['State'].notna() & (df['State'] != 'Unknown')]
        .drop_duplicates('City')
        .set_index('City')['State']
        .to_dict()
    )
    
    # Step 2: Fill missing or 'Unknown' states using city mapping
    df['State'] = df.apply(
        lambda row: city_state_map.get(row['City'], row['State'])
        if row['State'] in [None, '', 'Unknown', np.nan] else row['State'],
        axis=1
    )
    
    # # Step 3: Use Nominatim only for those still Unknown (slow, so optional)
    # df['full_address'] = df['Address'] + ', ' + df['City']
    
    # for idx, row in df[df['State'] == 'Unknown'].iterrows():
    #     state = get_state_from_nominatim(row['City'])
    #     df.at[idx, 'State'] = state
    #     time.sleep(1)  # Be nice to Nominatim!
    
    # # Build full address
    # df['full_address'] = df['Address'] + ', ' + df['City']
    
    # Apply only to rows where State is still 'Unknown'
    for idx, row in df[df['State'] == 'Unknown'].iterrows():
        state = get_state_from_nominatim_cached(row['City'] + ', India')
        if state == "Unknown":
            pincode = extract_pincode(row['Address'])
            state = get_state_from_nominatim_cached(pincode)
            
        df.at[idx, 'State'] = state
        time.sleep(1)  # Respect Nominatim rate limit
    
    # # Save final cache to file
    # save_cache()
    
    ###------------------ DATA SAVING SECTION ------------------###
    
    filename = f"ola_showrooms_{today}.csv"
    df.to_csv(filename, index=False)
    print("Done! ✅ Updated DataFrame saved as new_ola.csv")
    
