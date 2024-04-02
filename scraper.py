from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from dotenv import load_dotenv
import os
from urlextract import URLExtract
from ownserver_logger import send_message_to_discord, send_exception_to_discord
import time

load_dotenv()

ash_webhook_url = os.getenv('ash_webhook_url')
blacklisted_names = ['unknown', 'orca']

def scrape(contract: str):
    driver = None
    twitter_link = ''
    try:
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')  # Helps prevent Chrome crash in Docker container

        chrome_driver_path = "/usr/local/bin/chromedriver"

        # Explicit use of ChromeDriver path
        service = Service(executable_path=chrome_driver_path)

        driver = webdriver.Chrome(service=service, options=options)
        driver.set_page_load_timeout(120)
        driver.get(f'https://www.dexlab.space/mintinglab/spl-token/{contract}')
        send_message_to_discord(f"Scraping [{contract}](https://www.dexlab.space/mintinglab/spl-token/{contract})", ash_webhook_url)
        time.sleep(5)

        wait = WebDriverWait(driver, 10)
        
        try:
            name_element = wait.until(EC.presence_of_element_located((
                By.XPATH,
                "//div[contains(@class, 'py-4 sm:py-5 sm:grid sm:grid-cols-3 sm:gap-4')]//dt[contains(@class, 'text-sm font-medium text-gray-300') and contains(text(), 'Name')]/following-sibling::dd[contains(@class, 'mt-1 text-sm text-gray-100 sm:mt-0 sm:col-span-2')]"
            )))
        except:
            name_element = ''
        name = name_element.text if name_element else ''

        if any(blacklisted_name.lower() in name.lower() for blacklisted_name in blacklisted_names):
            send_message_to_discord(f"Blacklisted name: {name} {contract}", ash_webhook_url)
            return False

        try:
            description_element = wait.until(EC.presence_of_element_located((
                By.XPATH,
                '//div[@class="py-4 sm:py-5 sm:grid sm:grid-cols-3 sm:gap-4"]/dd[@class="mt-1 text-sm text-gray-100 sm:mt-0 sm:col-span-2 break-words"]'
            )))
        except:
            description_element = ''
        description = description_element.text if description_element else ''

        extractor = URLExtract()
        urls = extractor.find_urls(description)
        
        for url in urls:
            if "x.com" in url or "twitter.com" in url:
                return url

        links_elements = driver.find_elements(By.XPATH, "//div[contains(@class, 'mt-5 flex flex-col items-end justify-center sm:mt-0 text-[18px] font-bold')]//a")
        for element in links_elements:
            href = element.get_attribute('href').lower()
            if 'twitter' in href or 'x.com' in href:
                twitter_link = href
                break

        return twitter_link

    except Exception as e:
        send_exception_to_discord(e, ash_webhook_url)

        return twitter_link
    finally:
        if driver:
            driver.quit()

    return twitter_link
