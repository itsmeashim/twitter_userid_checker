from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from dotenv import load_dotenv
import os
import time
from urlextract import URLExtract
from ownserver_logger import send_message_to_discord, send_exception_to_discord

load_dotenv()

ash_webhook_url = os.getenv('ash_webhook_url')

blacklisted_names = ['unknown', 'orca']

def scrape(contract: str):
    driver = None
    try:
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')

        driver = webdriver.Chrome(options=options)
        driver.get(f'https://www.dexlab.space/mintinglab/spl-token/{contract}')
        send_message_to_discord(f"Scraping [{contract}](https://www.dexlab.space/mintinglab/spl-token/{contract})", ash_webhook_url)

        time.sleep(5)

        wait = WebDriverWait(driver, 10)
        name = ''
        try:
            element = wait.until(EC.presence_of_element_located((
                By.XPATH,
                "//div[contains(@class, 'py-4 sm:py-5 sm:grid sm:grid-cols-3 sm:gap-4')]//dt[contains(@class, 'text-sm font-medium text-gray-300') and contains(text(), 'Name')]/following-sibling::dd[contains(@class, 'mt-1 text-sm text-gray-100 sm:mt-0 sm:col-span-2')]"
            )))
            name = element.text
        except:
            pass

        # Efficient check for blacklisted names
        isBlacklisted = any(blacklisted_name.lower() in name.lower() for blacklisted_name in blacklisted_names)
        
        if isBlacklisted:
            send_message_to_discord(f"Blacklisted name: {name} {contract}", ash_webhook_url)
            return False

        description = ''
        try:
            element = wait.until(EC.presence_of_element_located((By.XPATH, '//div[@class="py-4 sm:py-5 sm:grid sm:grid-cols-3 sm:gap-4"]/dd[@class="mt-1 text-sm text-gray-100 sm:mt-0 sm:col-span-2 break-words"]')))
            description = element.text
        except:
            pass

        extractor = URLExtract()
        urls = extractor.find_urls(description)
        urls = [url for url in urls]
        
        for url in urls:
            if "x.com" in url or "twitter.com" in url:
                return url

        twitter_link = ''
        links_elements = driver.find_elements(By.XPATH, "//div[contains(@class, 'mt-5 flex flex-col items-end justify-center sm:mt-0 text-[18px] font-bold')]//a")
        for element in links_elements:
            href = element.get_attribute('href').lower()
            if 'twitter' in href or 'x.com' in href:
                twitter_link = href
                break

    except Exception as e:
        send_exception_to_discord(e, ash_webhook_url)
    finally:
        if driver:
            driver.quit()

    return twitter_link