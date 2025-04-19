import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    StaleElementReferenceException,
    NoSuchElementException,
)
from bs4 import BeautifulSoup
from datetime import datetime

# Configuration
HEADLESS = True  # Set to True to run in headless mode
WAIT_TIME = 10
MAX_RETRIES = 3
URL = "https://dealers.heromotocorp.com/"

# Initialize WebDriver
def start_browser():
    options = Options()
    if HEADLESS:
        options.add_argument("--headless=new")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0")
    
    # Do NOT use user-data-dir or profile directories
    # This avoids conflicts in CI like GitHub Actions

    prefs = {
        "profile.managed_default_content_settings.images": 2,
        "profile.default_content_setting_values.notifications": 2,
        "profile.default_content_setting_values.geolocation": 2,
    }
    options.add_experimental_option("prefs", prefs)

    # Use Service() without specifying chromedriver path if you're using latest version via PATH
    driver = webdriver.Chrome(service=Service(), options=options)
    driver.get(URL)
    return driver


# Wait for an element to be present
def wait_for_element(driver, by, value, timeout=WAIT_TIME):
    return WebDriverWait(driver, timeout).until(EC.presence_of_element_located((by, value)))

# Scrape dealer information
def scrape_dealers(driver, state_name, city_name):
    dealers = []
    while True:
        time.sleep(2)  # Wait for the page to load
        soup = BeautifulSoup(driver.page_source, "html.parser")
        dealer_elements = soup.find_all("div", class_="store-info-box")
        for dealer in dealer_elements:
            try:
                name = dealer.find("li", class_="outlet-name").get_text(strip=True)
                address = dealer.find("li", class_="outlet-address").get_text(strip=True)
                phone = dealer.find("li", class_="outlet-phone").get_text(strip=True)
                dealers.append({
                    "Showroom Name": name,
                    "Address": address,
                    "Phone": phone,
                    "City": city_name,
                    "State": state_name
                })
            except AttributeError:
                continue

        # Check for the presence of the "Next" button
        try:
            next_button = driver.find_element(By.LINK_TEXT, "Next")
            if "disabled" in next_button.get_attribute("class"):
                break
            next_button.click()
        except NoSuchElementException:
            break
    return dealers

# Main scraping function
def main():
    driver = start_browser()
    data = []
    try:
        # Wait for state dropdown to load
        wait_for_element(driver, By.ID, "OutletState")
        state_dropdown = Select(driver.find_element(By.ID, "OutletState"))
        for state_index in range(1, len(state_dropdown.options)):
            for attempt in range(MAX_RETRIES):
                try:
                    state_dropdown = Select(driver.find_element(By.ID, "OutletState"))
                    state_option = state_dropdown.options[state_index]
                    state_value = state_option.get_attribute("value")
                    state_name = state_option.text.strip()
                    if not state_value:
                        continue
                    state_dropdown.select_by_value(state_value)
                    time.sleep(2)  # Wait for city dropdown to load

                    # Wait for city dropdown to load
                    wait_for_element(driver, By.ID, "OutletCity")
                    city_dropdown = Select(driver.find_element(By.ID, "OutletCity"))
                    for city_index in range(1, len(city_dropdown.options)):
                        for city_attempt in range(MAX_RETRIES):
                            try:
                                city_dropdown = Select(driver.find_element(By.ID, "OutletCity"))
                                city_option = city_dropdown.options[city_index]
                                city_value = city_option.get_attribute("value")
                                city_name = city_option.text.strip()
                                if not city_value:
                                    continue
                                city_dropdown.select_by_value(city_value)
                                time.sleep(1)
                                # Click the search button
                                search_button = driver.find_element(By.XPATH, '//*[@id="OutletStoreLocatorSearchForm"]/div/div[2]/div[2]/input')
                                search_button.click()
                                dealers = scrape_dealers(driver, state_name, city_name)
                                data.extend(dealers)
                                break
                            except (StaleElementReferenceException, TimeoutException):
                                time.sleep(2)
                                continue
                    break
                except (StaleElementReferenceException, TimeoutException):
                    time.sleep(2)
                    continue
    finally:
        driver.quit()
        # Save data to CSV
        df = pd.DataFrame(data)
        today = datetime.today().strftime("%d-%m-%Y")
        filename = f"hero_showrooms_{today}.csv"
        df.to_csv(filename, index=False)
        print(f"Data saved to {filename}")

if __name__ == "__main__":
    main()
