import os 
from dotenv import load_dotenv
import logging
from functions import get_response, check_response
from ownserver_logger import send_exception_to_discord
import time
import random

logging.basicConfig(level=logging.INFO)

load_dotenv()

NEWTOKEN_ID = os.getenv("NEWTOKEN_ID")
guild_id = os.getenv("guild_id")
ash_webhook_url = os.getenv("ash_webhook_url")
toko_webhook_url = os.getenv("toko_webhook_url")

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