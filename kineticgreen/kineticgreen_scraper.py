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
import tempfile

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
user_data_dir = tempfile.mkdtemp()
options.add_argument(f"--user-data-dir={user_data_dir}")
# Optional: Disable image loading (better done via prefs)
prefs = {"profile.managed_default_content_settings.images": 2}
options.add_experimental_option("prefs", prefs)

###------------------ VARIABLES SECTION ------------------###

data = []

# Constants
today = datetime.today().strftime("%d-%m-%Y")
url = "https://www.kineticgreen.com/dealership"
MAX_RETRIES = 3  # Number of retries per pincode
RESTART_BROWSER_AFTER = 10  # Restart Browser every N cities
WAIT_TIME = 10  # Increased explicit wait time
DATA_SAVE_INTERVAL = 30  # Save every N cities
cities = [] # Save cities list here

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

# Function to scrape dealer details
def scrape_dealers(city, driver):
    """Extracts dealer details from the page source."""
    soup = BeautifulSoup(driver.page_source, "html.parser")
    dealers = []
    section = soup.find("section", class_="dealershipNearYou")
    container = section.find("div", class_="container")
    
    if "No result found." in container.text:
        dealers.append(["", "", "", city])
    else:
        showroom_list = container.find_all("li")
        # print(showroom_list.text)
        for showroom in showroom_list:
            name = showroom.find("h3").text.replace("\n","")
            address = showroom.find("div", class_="adressPopup").text.replace("\n","")
            phone = showroom.find("a", class_="mobNum").text.replace("\n","")

            dealers.append([name if name else "", address if address else "", phone if phone else "", city])
    return dealers
    
def search(city, i, driver, wait):

    drop_down = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="Dealers"]/div/h2/span/a')))
    drop_down.click()
    # print(f"Searching {city}")
    
    # Locate the input field first
    input = wait.until(EC.element_to_be_clickable((By.XPATH, f'/html/body/div[11]/ul/li[{i}]')))
    
    # click on the city
    input.click()
    time.sleep(2)

# Function to fetch cities from website
def city_fun():
    driver, wait = start_browser()
    driver.execute_script("window.scrollTo(0,100);")
    time.sleep(3)
    drop_down = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="Dealers"]/div/h2/span/a')))
    drop_down.click()
    time.sleep(3)
    soup = BeautifulSoup(driver.page_source, "html.parser")
    container = soup.find("div", class_="gs_ta_results")
    cities_list = container.find_all("li")
    for city in cities_list:
        cities.append(city.text)
    driver.quit()
    
# Main funtion to run the set a defined funtions in a order
def main():
    city_fun()
    
    driver, wait = start_browser()
    # print(cities)
    # print(len(cities))
    
    # for city in cities:
    for i, city in enumerate(cities):
        if i > 0 and i % RESTART_BROWSER_AFTER == 0:
            print("[INFO] Restarting browser to free memory...")
            driver.quit()
            # time.sleep(5)
            driver, wait = start_browser()
        retry_count = 0
        while retry_count < MAX_RETRIES:
            try:
                # Perform the search
                search(city, i+1, driver, wait)
                dealers = scrape_dealers(city, driver)
                data.extend(dealers)
                print(f"✅ Success: {city}")
    
                break  # If success, exit retry loop

            except:
                print("retrying")
                retry_count += 1

                if retry_count == MAX_RETRIES:
                    print(f"❌ Skipping {city} after {MAX_RETRIES} retries")
                
    driver.quit()
main()
###------------------ DATA SAVING SECTION ------------------###

df = pd.DataFrame(data, columns=["Showroom Name", "Address", "Phone", "City"]).drop_duplicates()
filename = f"kineticgreen_showrooms_{today}.csv"
df.to_csv(filename, index=False)
