import requests
import json
from traceback import format_exception


def send_message_to_discord(message, webhook_url):

    # Creating the embed for the message
    data = {
        "embeds": [{
            "description": message,
            "color": 0x3498DB  # Blue color for informational message
        }]
    }

    # Sending the POST request to the Discord webhook
    response = requests.post(webhook_url, json=data)
    if response.status_code != 204:
        print(f"Request to Discord webhook failed with status code {response.status_code}")


def send_exception_to_discord(exception, webhook_url):
    if not isinstance(exception, Exception):
        print("Parameter must be an Exception.")
        return

    # Formatting the exception
    # exception_message = f"{type(exception).__name__}: {exception}"
    exception_message = "".join(format_exception(type(exception), exception, exception.__traceback__))

    # Creating the embed
    data = {
        "embeds": [{
            "title": "Exception Occurred",
            "description": f"```{exception_message}```",
            "color": 0xFF0000  # Red color for error
        }]
    }

    # Sending the POST request to the Discord webhook
    response = requests.post(webhook_url, json=data)
    if response.status_code != 204:
        print(f"Request to Discord webhook failed with status code {response.status_code}")