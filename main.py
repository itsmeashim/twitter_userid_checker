from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import time
import re
from urlextract import URLExtract
import asyncio
from ownserver_logger import *
import random
import requests
import json
from pymongo import MongoClient
import os 
from dotenv import load_dotenv
import logging

logging.basicConfig(level=logging.INFO)

load_dotenv()

NEWTOKEN_ID = os.getenv("NEWTOKEN_ID")
guild_id = os.getenv("guild_id")
DC_TOKEN = os.getenv("DC_TOKEN")
ash_webhook_url = os.getenv("ash_webhook_url")
toko_webhook_url = os.getenv("toko_webhook_url")
MONGO_URI = os.getenv("MONGO_URI")

cluster = MongoClient(MONGO_URI)
db = cluster["discord_dexlabs"]
collection = db["twitter_match"]

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
        send_message_to_discord(f"Error occurred while scraping {contract}:\n", ash_webhook_url)
        send_exception_to_discord(e, ash_webhook_url)
        driver.quit()

    return twitter_link

def get_response(channel_id):
    try:
        data_reversed = []
        url = f"https://discord.com/api/v9/channels/{channel_id}/messages"
        header = {
            'authorization': DC_TOKEN
        }
        response = requests.get(url, headers=header).json()
        if isinstance(response, list):
            data_reversed = response[::-1]
        # print(data_reversed)
        return data_reversed
    except Exception as e:
        send_exception_to_discord(e, ash_webhook_url)
        return []

def send_alert_to_discord(guild_id, channel_id, message_id, embed, token_address, results, webhook_url=toko_webhook_url):

    response = ""
    
    for result in results:
        token_address = result['token']
        creator = result['creator']
        twitter_username = result['twitter_username']
        msg_id = result['message_id']
        
        response += f"Token Address: {token_address}\nCreator: {creator}\nTwitter Username: {twitter_username}\n[Message](https://discord.com/channels/{guild_id}/{channel_id}/{msg_id})\n\n"
        
    link = f"https://discord.com/channels/{guild_id}/{channel_id}/{message_id}"

    embed_pd = {
        "title": f"Contract address with same twitter id {token_address} Found!",
        "description": response,
        "url": link
    }

    data = {
        "embeds": [embed_pd, embed]
    }
    requests.post(webhook_url, json=data)

def process_message(message):
    try:
        embeds = message.get('embeds', {})
        embed = embeds[0] if len(embeds) > 0 else ""
        if not embed:
            return "", "", ""
        message_title = embed['title'] if 'title' in embed else ''
        message_desc = embed['description'] if 'description' in embed else ''
        message_fields = embed['fields'] if 'fields' in embed else ''
        print(f"Message title: {message_title}")

        fields_values = [list(field.values()) for field in message_fields]
        token_address = ''
        token_address = [field['value'].split('](')[0].rstrip(')').strip('[') for field in embed['fields'] if field['name'] == "Token Address"]

        print(f"Token Address1: {token_address[0]}")     

        creator_address = [field['value'].split('](')[0].rstrip(')').strip('[') for field in embed['fields'] if field['name'] == "Creator"]

        send_message_to_discord(f"Token Address: {token_address[0]} - Title: {message_title}", ash_webhook_url)
        return token_address[0], creator_address[0], embed
    except Exception as e:
        send_exception_to_discord(e, ash_webhook_url)
        return "", "", ""


def get_twitter_id(username):
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    
    driver = webdriver.Chrome(options=options)
    driver.get("https://ilo.so/twitter-id/")

    username_input = driver.find_element(By.ID, "id_username")
    username_input.send_keys(username)

    username_input.send_keys(Keys.RETURN)

    try:
        WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.ID, "user_id")))
        
        user_id_element = driver.find_element(By.ID, "user_id")
        user_id = user_id_element.text
    except:
        driver.quit()
        return None

    driver.close()

    return user_id

def doesIdMatch(user_id):
    if not user_id:
        return False
    result = collection.find_one({"twitter_id": f"{user_id}"})
    return result != None

def check_response(response, prev_id, latest_message_id, channel_id):
    try:
        latest_message = response
        prev_id = latest_message_id if not prev_id else prev_id
        new_id = int(latest_message['id'])

        if int(prev_id) < int(new_id):
            token_address, creator_address, embed = process_message(latest_message)
            if not token_address:
                return new_id

            twitter_link = scrape(token_address)

            if not twitter_link:
                return new_id

            twitter_username = twitter_link.split("/")[-1].split("?")[0]
            print(f"Twitter username: {twitter_username}")

            user_id = get_twitter_id(twitter_username)
            print(f"Twitter id: {user_id}")

            if not user_id:
                return new_id

            isMatch = doesIdMatch(user_id)
            print(f"Is match: {isMatch}")

            data = {
                "twitter_username": twitter_username,
                "creator": creator_address,
                "token": token_address,
                "message_id": new_id
            }

            if isMatch:
                hehe = collection.update_one({"twitter_id": user_id}, {"$push": {"tokens": data}})
                results = collection.find_one({"twitter_id": user_id})
                results = list(results['tokens'])
                print(f"Results: {results}")
                send_alert_to_discord(guild_id, channel_id, new_id, embed, token_address, results, toko_webhook_url)
                send_message_to_discord(f"Contract address with same twitter id {token_address} Found!", ash_webhook_url)
            else:
                collection.insert_one({"twitter_id": f"{user_id}", "tokens": [data]})
                send_message_to_discord(f"Contract address with new twitter link {token_address} Found!", ash_webhook_url)
            return new_id

        return prev_id
    except Exception as e:
        send_exception_to_discord(e, ash_webhook_url)
        return new_id

if __name__ == "__main__":
    i = 0
    new_token_prev_id = 0

    while True:
        # Increment check count and print status
        i += 1
        print(f"Checking Now, times checked: {i}")
        try:
            # Fetch messages from Discord
            new_token_response = get_response(NEWTOKEN_ID)

            for response in new_token_response:
                latest_message_id = new_token_response[-1]['id']
                new_token_new_id = check_response(response, new_token_prev_id, latest_message_id, NEWTOKEN_ID)
                new_token_prev_id = new_token_new_id if new_token_new_id else new_token_prev_id
        except Exception as e:
            send_exception_to_discord(e, ash_webhook_url)
            continue

        if not i == 1:
            time.sleep(random.uniform(5, 7))