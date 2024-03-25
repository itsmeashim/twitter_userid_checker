from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from dotenv import load_dotenv
from ownserver_logger import *
import os
import time
from urlextract import URLExtract

load_dotenv()

ash_webhook_url = os.getenv('ash_webhook_url')

blacklisted_names = ['unknown', 'orca']
def scrape(contract: str):
    try:
        twitter_link = ""

        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')

        driver = webdriver.Chrome(options=options)

        driver.get(f'https://www.dexlab.space/mintinglab/spl-token/{contract}')
        send_message_to_discord(f"Scraping [{contract}](https://www.dexlab.space/mintinglab/spl-token/{contract})", ash_webhook_url)
        time.sleep(5)

        wait = WebDriverWait(driver, 10)

        # print the upper xpath
        try:
            element = wait.until(EC.presence_of_element_located((By.XPATH, '//div[@class="py-4 sm:py-5 sm:grid sm:grid-cols-3 sm:gap-4"]/dt[@class="text-sm font-medium text-gray-300"]')))
            print(element.text)
        except Exception as e:
            send_message_to_discord(f"Error occurred while scraping and reading description {contract}:\n", ash_webhook_url)
            driver.quit()
            return False

        try:
            # name = wait.until(EC.presence_of_element_located((By.XPATH, '//div[@class="py-4 sm:py-5 sm:grid sm:grid-cols-3 sm:gap-4"]/dt[@class="text-sm font-medium text-gray-300"](@contains text, "Name")/dd[@class="mt-1 text-sm text-gray-100 sm:mt-0 sm:col-span-2"]')))
            element = wait.until(EC.presence_of_element_located((
                By.XPATH, 
                "//div[contains(@class, 'py-4 sm:py-5 sm:grid sm:grid-cols-3 sm:gap-4')]//dt[contains(@class, 'text-sm font-medium text-gray-300') and contains(text(), 'Name')]/following-sibling::dd[contains(@class, 'mt-1 text-sm text-gray-100 sm:mt-0 sm:col-span-2')]"
            )))
            name = element.text
            print(f"Name: {name}")
        except:
            name = ''
    
        isBlacklisted = [True for blacklisted_name in blacklisted_names if blacklisted_name.lower() in name.lower()]    
        
        if isBlacklisted:
            print(f"Blacklisted name: {name}")
            send_message_to_discord(f"Blacklisted name: {name} {contract}", ash_webhook_url)
            driver.quit()
            return False

        try:
            element = wait.until(EC.presence_of_element_located((By.XPATH, '//div[@class="py-4 sm:py-5 sm:grid sm:grid-cols-3 sm:gap-4"]/dd[@class="mt-1 text-sm text-gray-100 sm:mt-0 sm:col-span-2 break-words"]')))
            description = element.text
        except:
            description = ''

        print(f"Description: {description}")

        extractor = URLExtract()
        urls = extractor.find_urls(description)
        urls = [url for url in urls]
        
        for url in urls:
            if "x.com" in url or "twitter.com" in url:
                return url

        links_elements = driver.find_elements(By.XPATH, "//div[contains(@class, 'mt-5 flex flex-col items-end justify-center sm:mt-0 text-[18px] font-bold')]//a")

        telegram_link = ''
        website_link = ''
        for element in links_elements:
            href = element.get_attribute('href').lower()
            if 'twitter' in href or 'x.com' in href:
                twitter_link = href
            elif 't.me' in href:
                telegram_link = href
            else:
                website_link = href

        print(f"Website: {website_link if website_link else 'Not found'}")
        print(f"Twitter: {twitter_link if twitter_link else 'Not found'}")
        print(f"Telegram: {telegram_link if telegram_link else 'Not found'}")

        driver.quit()

    except Exception as e:
        send_exception_to_discord(e, ash_webhook_url)
        driver.quit()

    return twitter_link