###------------------ IMPORT SECTION ------------------###

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup
from datetime import datetime
import pandas as pd
import time

###------------------ CONFIGURATION SECTION ------------------###

# Setup Chrome WebDriver - Configure Selenium to use Chrome
options = Options()
options.add_argument("--headless")  # Use old headless mode for better compatibility
options.add_argument("--disable-popup-blocking")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--window-size=1920,1080")
options.add_argument("user-agent=Mozilla/5.0")

prefs = {
    "profile.managed_default_content_settings.images": 2,
    "profile.default_content_setting_values.notifications": 2,
    "profile.default_content_setting_values.geolocation": 2
}
options.add_experimental_option("prefs", prefs)

###------------------ VARIABLES SECTION ------------------###

today = datetime.today().strftime("%d-%m-%Y")
url = "https://www.yamaha-motor-india.com/dealer-network.html"
data = []

MAX_RETRIES = 2
WAIT_TIME = 15

###------------------ PROCESS SECTION ------------------###

def start_browser():
    driver = webdriver.Chrome(service=Service(), options=options)
    driver.get(url)
    wait = WebDriverWait(driver, WAIT_TIME)
    time.sleep(2)  # Initial load
    return driver, wait

def scrape_dealers(driver, state, city):
    dealers = []
    soup = BeautifulSoup(driver.page_source, "html.parser")
    container = soup.find("div", id="all_search_result")
    showroom_list = soup.find_all("div", class_="slick-list draggable")
    
    for showroom in showroom_list:
        try:
            details = showroom.find("div", class_="dealers-info-content")
            name = details.find("h4").text.strip()

            address_icon = details.find("i", class_="fa-regular fa-map")
            phone_icon = details.find("i", class_="fa-solid fa-mobile-screen")

            address = address_icon.next_sibling.text.strip() if address_icon else ""
            phone = phone_icon.next_sibling.text.strip() if phone_icon else ""

            dealers.append([name, address, phone, city, state])
            print(f"[{state} - {city}] {name}")
        except:
            continue
    return dealers

def select_state_city(driver, wait):
    WebDriverWait(driver, WAIT_TIME).until(EC.presence_of_element_located((By.ID, "type")))
    type_dropdown = Select(driver.find_element(By.ID, "type"))
    type_dropdown.select_by_value("sales")
    time.sleep(2)

    state_dropdown = Select(wait.until(EC.presence_of_element_located((By.ID, "state"))))
    wait.until(lambda d: len(state_dropdown.options) > 1)

    for state_option in state_dropdown.options:
        state_value = state_option.get_attribute("value")
        state_name = state_option.text.strip()

        if not state_value or state_name == "-- State --":
            continue

        try:
            state_dropdown = Select(driver.find_element(By.ID, "state"))
            state_dropdown.select_by_value(state_value)
            print(f"\n📍 State: {state_name}")
            time.sleep(2)

            city_dropdown = Select(wait.until(EC.presence_of_element_located((By.ID, "city"))))
            wait.until(lambda d: len(city_dropdown.options) > 1)

            for city_option in city_dropdown.options:
                city_value = city_option.get_attribute("value")
                city_name = city_option.text.strip()

                if not city_value or city_name == "-- City --":
                    continue

                try:
                    city_dropdown = Select(driver.find_element(By.ID, "city"))
                    city_dropdown.select_by_value(city_value)
                    print(f"  → City: {city_name}")
                    time.sleep(3)

                    dealers = scrape_dealers(driver, state_name, city_name)
                    data.extend(dealers)
                except Exception as e:
                    print(f"❌ Error selecting city {city_name}: {e}")
                    continue
        except Exception as e:
            print(f"❌ Error selecting state {state_name}: {e}")
            continue

def main():
    driver, wait = start_browser()
    try:
        select_state_city(driver, wait)
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
    df = pd.DataFrame(data, columns=["Showroom Name", "Address", "Phone", "City", "State"]).drop_duplicates()
    filename = f"yamaha_showrooms_{today}.csv"
    df.to_csv(filename, index=False)
    print(f"\n✅ Done! Saved data to {filename}")
