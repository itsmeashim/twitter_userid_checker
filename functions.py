import requests
import json
from metadata_api import get_twitter_link
from twitter_api import doesIdMatch, get_twitter_id, doesBothMatch
from scraper import scrape
from ownserver_logger import send_message_to_discord, send_exception_to_discord
from connection_setter import collection
from dotenv import load_dotenv
import os
import logging

logging.basicConfig(level=logging.INFO)

load_dotenv()

toko_webhook_url = os.getenv('toko_webhook_url')
ash_webhook_url = os.getenv('ash_webhook_url')
guild_id = os.getenv('guild_id')
DC_TOKEN = os.getenv('DC_TOKEN')

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

def process_message(message):
    try:
        embeds = message.get('embeds', {})
        embed = embeds[0] if len(embeds) > 0 else ""
        if not embed:
            return "", "", ""
        message_title = embed['title'] if 'title' in embed else ''
        message_desc = embed['description'] if 'description' in embed else ''
        message_fields = embed['fields'] if 'fields' in embed else ''
        logging.INFO(f"Message Title: {message_title}")

        fields_values = [list(field.values()) for field in message_fields]
        token_address = ''
        token_address = [field['value'].split('](')[0].rstrip(')').strip('[') for field in embed['fields'] if field['name'] == "Token Address"]

        logging.INFO(f"Token Address: {token_address[0]}")

        creator_address = [field['value'].split('](')[0].rstrip(')').strip('[') for field in embed['fields'] if field['name'] == "Creator"]

        send_message_to_discord(f"Token Address: {token_address[0]} - Title: {message_title}", ash_webhook_url)
        return token_address[0], creator_address[0], embed
    except Exception as e:
        send_exception_to_discord(e, ash_webhook_url)
        return "", "", ""

def check_response(response, prev_id, latest_message_id, channel_id):
    try:
        latest_message = response
        prev_id = latest_message_id if not prev_id else prev_id
        new_id = int(latest_message['id'])

        if int(prev_id) < int(new_id):
            token_address, creator_address, embed = process_message(latest_message)
            if not token_address:
                return new_id

            twitter_link = get_twitter_link(token_address)

            if 'err404' in twitter_link:
                twitter_link = ""
                twitter_link = scrape(token_address)

            if not twitter_link:
                return new_id

            twitter_username = twitter_link.split("/")[-1].split("?")[0]
            logging.INFO(f"Twitter username: {twitter_username}")

            send_message_to_discord(f"Twitter username: {twitter_username}", ash_webhook_url)

            user_id = get_twitter_id(twitter_username)
            logging.INFO(f"Twitter id: {user_id}")

            if not user_id:
                return new_id

            isMatch = doesIdMatch(user_id, twitter_username)
            logging.INFO(f"Is match: {isMatch}")

            bothMatches = doesBothMatch(user_id)
            if bothMatches:
                send_message_to_discord(f"Contract address with same twitter id {token_address} Found!", ash_webhook_url)
                return new_id

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
                logging.INFO(f"Results: {results}")
                send_alert_to_discord(guild_id, channel_id, new_id, embed, token_address, results, toko_webhook_url)
                send_message_to_discord(f"Contract address with same twitter id but different username {token_address} Found!", ash_webhook_url)
            else:
                collection.insert_one({"twitter_id": f"{user_id}", "tokens": [data]})
                send_message_to_discord(f"Contract address with new twitter link {token_address} Found!", ash_webhook_url)
            return new_id
        return prev_id
    except Exception as e:
        send_exception_to_discord(e, ash_webhook_url)
        return new_id