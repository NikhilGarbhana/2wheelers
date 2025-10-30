# ###------------------ IMPORT SECTION ------------------###

# # Import required libraries
# from selenium import webdriver
# from selenium.webdriver.chrome.service import Service
# from selenium.webdriver.chrome.options import Options
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.common.keys import Keys
# from selenium.webdriver.support.ui import Select
# from selenium.webdriver.support import expected_conditions as EC
# from selenium.webdriver.common.action_chains import ActionChains
# from selenium.common.exceptions import UnexpectedAlertPresentException, TimeoutException
# from selenium.webdriver.common.alert import Alert

# import pandas as pd
# import time
# import csv
# import requests
# from bs4 import BeautifulSoup
# from datetime import datetime
# import re

# ###------------------ CONFIGURATION SECTION ------------------###

# # Setup Chrome WebDriver - Configure Selenium to use Chrome
# options = Options()
# # options.add_argument("--headless=new")  # Correct syntax for headless
# options.add_argument("--disable-popup-blocking")
# options.add_argument("--disable-gpu")
# options.add_argument("--no-sandbox")
# options.add_argument("--disable-dev-shm-usage")
# options.add_argument("--start-maximized")
# options.add_argument("user-agent=Mozilla/5.0")

# # Optional: Disable image loading (better done via prefs)
# # prefs = {"profile.managed_default_content_settings.images": 2}
# # options.add_experimental_option("prefs", prefs)

# # prefs = {
# #   "profile.managed_default_content_settings.images": 2,
# #   "profile.default_content_setting_values.notifications": 2,
# #   "profile.default_content_setting_values.geolocation": 2
# # }
# # options.add_experimental_option("prefs", prefs)

# ###------------------ VARIABLES SECTION ------------------###

# today = datetime.today().strftime("%d-%m-%Y")

# url = "https://dealers.heromotocorp.com/"

# # Store showroom data"
# data = []
# state_cities = {}

# # Constants
# MAX_RETRIES = 2  # Number of retries per pincode
# RESTART_BROWSER_AFTER = 10  # Restart Chrome every N pincodes
# WAIT_TIME = 10  # Increased explicit wait time
# DATA_SAVE_INTERVAL = 10  # Save every N pincodes

# ###------------------ PROCESS SECTION ------------------###

# # Funtion to start a browser
# def start_browser():
#     """Starts a new browser session."""
#     driver = webdriver.Chrome(service=Service(), options=options)
#     driver.maximize_window()
#     wait = WebDriverWait(driver, WAIT_TIME, poll_frequency=0.5)

#     driver.get(url)
#     time.sleep(5)  # Initial load wait
    
#     return driver, wait

# # Function to scrape the showrooms from particular city
# def scrape_dealers(driver, wait, city, state):
#     dealers = []
#     while True:
#         page_source = driver.page_source
#         soup = BeautifulSoup(page_source, "html.parser")
        
#         container = soup.find("div", class_="outlet-list")
#         showroom_list = container.find_all("div", class_="store-info-box")
#         if showroom_list:
#             for showroom in showroom_list:
#                 name = showroom.find("li", class_="outlet-name").text.strip()
#                 address = showroom.find("li", class_="outlet-address").text.strip()
#                 phone = showroom.find("li", class_="outlet-phone").text.strip()
#                 print([name if name else "", address if address else "", phone if phone else "", city, state])
#                 dealers.append([name if name else "", address if address else "", phone if phone else "", city, state])
                
#         # Check for "Next" button
#         try:
#             next_button = WebDriverWait(driver, 3).until(EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Next')]")))

#             # Check if it's disabled or not present
#             if 'disabled' in next_button.get_attribute("class").lower():
#                 break

#             # Scroll to and click the next button
#             driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_button)
#             time.sleep(1)
#             next_button.click()
#             time.sleep(2)  # Give it time to load new content

#         except Exception as e:
#             print("No more pages or error while clicking next")
#             break
#     return dealers
    
# # Function to select state and city
# def select_state_city(driver, wait):
#     while True:
#         # try:
#         # Wait until the element is present
#         # target_element = WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, "/html/body/section[2]/div[2]")))
#         target_element = driver.find_element(By.XPATH, "/html/body/section[2]/div[2]")
        
#         # Scroll to the element using JavaScript
#         driver.execute_script("arguments[0].scrollIntoView({ behavior: 'smooth', block: 'center' });", target_element)
        
#         # Get the Select object from the state dropdown
#         state_dropdown_ele = wait.until(EC.presence_of_element_located((By.ID, "OutletState")))
#         state_dropdown = Select(state_dropdown_ele)

#         if len(state_dropdown.options)>1:
#             break
#         # except:
#         #     driver.refresh()
#         #     time.sleep(10)
    
#     # for state in state_dropdown.options):
#     for index in range(len(state_dropdown.options)):
        
#         # Wait until the element is present
#         target_element = WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, "/html/body/section[2]/div[2]")))
        
#         # Scroll to the element using JavaScript
#         driver.execute_script("arguments[0].scrollIntoView({ behavior: 'smooth', block: 'center' });", target_element)

#         # Get the Select object from the state dropdown
#         state_dropdown_ele = wait.until(EC.presence_of_element_located((By.ID, "OutletState")))
#         state_dropdown = Select(state_dropdown_ele)
        
#         state_value = state_dropdown.options[index].get_attribute("value")
#         if state_value == '':
#             continue
#         state_dropdown.select_by_value(state_value)
#         state_name = state_dropdown.options[index].text
#         print(state_name)

#         while True:
            
#             # Get the Select object from the state dropdown
#             city_dropdown_ele = wait.until(EC.presence_of_element_located((By.ID, "OutletCity")))
#             city_dropdown = Select(city_dropdown_ele)
    
#             if len(city_dropdown.options)>1:
#                 break
                
#         # for city in city_dropdown.options:
#         for index in range(len(city_dropdown.options)):
            
#             # Wait until the element is present
#             target_element = WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, "/html/body/section[2]/div[2]")))
            
#             # Scroll to the element using JavaScript
#             driver.execute_script("arguments[0].scrollIntoView({ behavior: 'smooth', block: 'center' });", target_element)

#             # Get the Select object from the state dropdown
#             city_dropdown_ele = wait.until(EC.presence_of_element_located((By.ID, "OutletCity")))
#             city_dropdown = Select(city_dropdown_ele)
            
#             city_value = city_dropdown.options[index].get_attribute("value")
#             if city_value == '':
#                 continue
#             city_dropdown.select_by_value(city_value)
#             city_name = city_dropdown.options[index].text
#             print(city_name)
#             # driver.execute_script("window.scrollTo(0,500);")
#             submit = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="OutletStoreLocatorSearchForm"]/div/div[2]/div[2]/input')))
#             submit.click()
#             time.sleep(3)
            
#             # Wait until the element is present
            
#             # target_container = WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, "/html/body/section[3]/div")))
            
#             # # Scroll to the element using JavaScript
#             # driver.execute_script("arguments[0].scrollIntoView({ behavior: 'smooth', block: 'center' });", target_container)
            
#             dealers = scrape_dealers(driver, wait, city_name, state_name)
#             data.extend(dealers)
        
    
# # Function to run the process step by step
# def main():
#     driver, wait = start_browser()
    
#     select_state_city(driver,wait)

#     driver.quit()
    
# if __name__ == "__main__":
#     main()
    
#     df = pd.DataFrame(data, columns=["Showroom Name", "Address", "Phone", "City", "State"]).drop_duplicates()
        
#     # Save updated file
#     filename = f"hero_showrooms_{today}.csv"
#     df.to_csv(filename, index=False)
#     print(f"Done! ✅ Updated DataFrame saved as {filename}")


import time
import csv
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

# ---------------- CONFIG ----------------
URL = "https://dealers.heromotocorp.com/"  # 👉 Replace with the target website URL
WAIT_TIME = 10
OUTPUT_FILE = "hero_dealers.csv"

options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
options.add_argument("--disable-notifications")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

# ---------------- HELPERS ----------------
def start_browser():
    """Starts a new Chrome browser session and returns driver + wait."""
    driver = webdriver.Chrome(service=Service(), options=options)
    driver.get(URL)
    time.sleep(5)
    wait = WebDriverWait(driver, WAIT_TIME, poll_frequency=0.5)
    return driver, wait


def safe_click(driver, element):
    """Scrolls to element and clicks it safely using JS (avoids click interception)."""
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
    time.sleep(0.3)
    driver.execute_script("arguments[0].click();", element)


def click_dropdown_option(driver, wait, label_text, option_text):
    """Clicks a dropdown option by its label name and visible text, with retries."""
    dropdown_xpath = f"//label[text()='{label_text}']/following-sibling::div[contains(@class, 'dropdown')]"
    option_xpath = f"//label[text()='{label_text}']/following-sibling::div//div[@class='item' and normalize-space(text())='{option_text}']"

    for attempt in range(3):
        try:
            dropdown = wait.until(EC.visibility_of_element_located((By.XPATH, dropdown_xpath)))
            safe_click(driver, dropdown)
            time.sleep(0.6)  # allow animation
            option = wait.until(EC.visibility_of_element_located((By.XPATH, option_xpath)))
            safe_click(driver, option)
            print(f"✅ Selected {label_text}: {option_text}")
            time.sleep(0.5)
            return True
        except Exception as e:
            print(f"⚠️ Attempt {attempt+1} to select {label_text}={option_text} failed → {e}")
            time.sleep(1)
    print(f"❌ Could not select {label_text}: {option_text}")
    return False


def get_dropdown_options(driver, wait, label_text):
    """Returns a list of all visible dropdown option texts under a given label."""
    dropdown_xpath = f"//label[text()='{label_text}']/following-sibling::div[contains(@class, 'dropdown')]"
    safe_click(driver, wait.until(EC.visibility_of_element_located((By.XPATH, dropdown_xpath))))
    time.sleep(0.5)

    items = wait.until(
        EC.presence_of_all_elements_located(
            (By.XPATH, f"//label[text()='{label_text}']/following-sibling::div//div[@class='item']")
        )
    )
    options = [i.text.strip() for i in items if i.text.strip() not in ("", "All")]
    safe_click(driver, driver.find_element(By.XPATH, dropdown_xpath))  # close dropdown
    print(f"📋 Found {len(options)} {label_text} options")
    return options


def scrape_dealers(driver, wait, city, state):
    """Scrapes dealer details for a given city & state."""
    dealers = []
    while True:
        soup = BeautifulSoup(driver.page_source, "html.parser")
        container = soup.find("div", class_="dl-branch-container-box")
        if not container:
            print("⚠️ No dealer container found.")
            break

        for showroom in container.find_all("a", class_="dl-branch"):
            name = showroom.find("h3", class_="branch-name")
            address = showroom.find("div", class_="branch-info")
            phone = showroom.find("span", class_="branch-wrap dl-call-click")

            record = [
                name.text.strip() if name else "",
                address.text.strip() if address else "",
                phone.text.strip() if phone else "",
                city,
                state,
            ]
            print(record)
            dealers.append(record)

        # Try clicking next button if exists
        try:
            next_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//li[contains(@class,'next')]/a")))
            if "disabled" in next_button.get_attribute("class").lower():
                break
            safe_click(driver, next_button)
            time.sleep(2)
        except TimeoutException:
            break

    return dealers


def select_state_city(driver, wait):
    """Main logic: loop through states, then cities."""
    all_data = []
    state_city_map = {}

    all_states = get_dropdown_options(driver, wait, "State")

    for state in all_states:
        print(f"\n🌎 Processing State: {state}")
        if not click_dropdown_option(driver, wait, "State", state):
            continue
        time.sleep(2)

        cities = get_dropdown_options(driver, wait, "City")
        state_city_map[state] = cities

        for city in cities:
            print(f"🏙️  Processing City: {city} ({state})")
            if not click_dropdown_option(driver, wait, "City", city):
                continue

            # Click Search
            try:
                search_btn = wait.until(EC.visibility_of_element_located((By.XPATH, "//button[contains(text(),'Search')]")))
                safe_click(driver, search_btn)
                time.sleep(2)
            except TimeoutException:
                print(f"⚠️ Search button not found for {city}, {state}")
                continue

            dealers = scrape_dealers(driver, wait, city, state)
            all_data.extend(dealers)

    return all_data, state_city_map


def save_to_csv(data, file_path):
    """Save scraped data to a CSV file."""
    header = ["Name", "Address", "Phone", "City", "State"]
    with open(file_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(data)
    print(f"\n📁 Data saved to {file_path} ({len(data)} rows)")


# ---------------- MAIN ----------------
def main():
    driver, wait = start_browser()
    try:
        all_data, state_cities = select_state_city(driver, wait)
        save_to_csv(all_data, OUTPUT_FILE)
        print(f"\n✅ Scraped {len(all_data)} dealers across {len(state_cities)} states.")
    except Exception as e:
        print("❌ Fatal error:", e)
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
