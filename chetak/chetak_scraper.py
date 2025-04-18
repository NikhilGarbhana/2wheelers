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
import json

###------------------ CONFIGURATION SECTION ------------------###


# Setup Chrome WebDriver - Configure Selenium to use Chrome
options = Options()
options.add_argument("--headless=new")  # Correct syntax for headless
options.add_argument("--disable-popup-blocking")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
# options.add_argument("--start-maximized")
options.add_argument("user-agent=Mozilla/5.0")

# Optional: Disable image loading (better done via prefs)
prefs = {"profile.managed_default_content_settings.images": 2}
options.add_experimental_option("prefs", prefs)

###------------------ VARIABLES SECTION ------------------###

today = datetime.today().strftime("%d-%m-%Y")

url = "https://www.chetak.com/#locate-dealer"

# Store showroom data"
data = []

# Constants
MAX_RETRIES = 2  # Number of retries per pincode
RESTART_BROWSER_AFTER = 10  # Restart Chrome every N pincodes
WAIT_TIME = 10  # Increased explicit wait time
DATA_SAVE_INTERVAL = 10  # Save every N pincodes
cities_df = pd.read_csv("cities.csv")
cities = cities_df['Value'].to_list()
nominatim_cache = {}

###------------------ PROCESS SECTION ------------------###

# Funtion to start a browser
def start_browser():
    """Starts a new browser session."""
    driver = webdriver.Chrome(service=Service(), options=options)
    driver.maximize_window()
    wait = WebDriverWait(driver, WAIT_TIME, poll_frequency=1)

    driver.get(url)
    time.sleep(2)  # Initial load wait
    
    return driver, wait

def extract_pincode(address):
    match = re.search(r'\b\d{6}\b', address)
    return match.group(0) if match else None
    
# Function to scrape dealer details
def scrape_dealers(city, driver):
    """Extracts dealer details from the page source."""
    soup = BeautifulSoup(driver.page_source, "html.parser")
    dealers = []
    section = soup.find("section", class_="location-map-section")
    showroom_list = section.find("div", class_="slick-track")
    # print(showroom_list.text)
    if showroom_list:
        showrooms = showroom_list.find_all("div", class_="dealer-location-card")
        for showroom in showrooms:
            name = showroom.find("h4", class_="dealer-location-card__title").text
            address = showroom.find("p", class_="dealer-location-card__address").text
            email = showroom.find("a", class_="dealer-location-card__email").text
            phone = showroom.find("a", class_="dealer-location-card__phone").text
            # print(name)
            # print(address)
            # print(phone)

            # dealers.append([name if name else "", address if address else "", email if email else "", phone if phone else "", city])
            dealers.append([name if name else "", address if address else "", email if email else "", phone if phone else ""])
    return dealers

def search(city, driver, wait):
    print(f"Searching {city}")
    
    # Locate the input field first
    input = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="findLocation"]')))
    
    # Scroll into view
    driver.execute_script("arguments[0].scrollIntoView(true);", input)
    
    # Clear input using JS
    driver.execute_script("arguments[0].value = '';", input)
    time.sleep(1)

    input.send_keys(city)
    time.sleep(1)

    input.send_keys(Keys.ARROW_DOWN)
    time.sleep(1)
    input.send_keys(Keys.ENTER)
    time.sleep(5)

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

    # for city in cities:
    for i, city in enumerate(cities):
        # if i > 0 and i % RESTART_BROWSER_AFTER == 0:
        #     print("[INFO] Restarting browser to free memory...")
        #     driver.quit()
        #     # time.sleep(5)
        #     driver, wait = start_browser()
        
        retry_count = 0
        while retry_count < MAX_RETRIES:
            try:
                # Perform the search
                search(city, driver, wait)
                time.sleep(3)
                wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="dealerLocatorMap"]/div/div/div/div[1]/div/div[1]/div[2]/div')))
                
                dealers = scrape_dealers(city, driver)
                data.extend(dealers)
                print(f"✅ Success: {city}")
                break
            except Exception as e:
                retry_count += 1
                # print(e)
                if retry_count == MAX_RETRIES:
                    break
                if "interactable" in str(e):
                    close_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@class="btn-close position-absolute top-0 end-0 m-3 close-btn"]')))
                    close_button.click()

    driver.quit()

if __name__ == "__main__":
    main()
    ###------------------ DATA SAVING SECTION ------------------###
    df = pd.DataFrame(data, columns=["Showroom Name", "Address", "Email", "Phone"]).drop_duplicates()
    
    # Drop empty showroom names
    df['Showroom Name'] = df['Showroom Name'].replace('', np.nan)
    df = df.dropna(subset=['Showroom Name'])
    df['State'] = ''
    
    # Apply only to rows where State is still ''
    for idx, row in df[df['State'] == ''].iterrows():
        pincode = extract_pincode(row['Address'])
        if pincode:
            state = get_state_from_nominatim_cached(pincode + ', India')
        else:
            state = get_state_from_nominatim_cached(row['Address'] + ', India')
            
        df.at[idx, 'State'] = state
        time.sleep(1)  # Respect Nominatim rate limit
        
    filename = f"chetak_showrooms_{today}.csv"
    df.to_csv(filename, index=False)
