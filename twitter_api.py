import requests
from connection_setter import collection
from dotenv import load_dotenv
import os
import json

load_dotenv()

bearer = os.getenv('bearer')
ct0 = os.getenv('ct0')
auth_token = os.getenv('auth_token')


# def get_twitter_id(username):
#     try:
#         url = 'https://tweeterid.com/ajax.php'
#         data = {'input': username}
#         response = requests.post(url, data=data)
#         print(response.text)
#         print(response)

#         if response.status_code == 200:
#             if "error" in response.text:
#                 return ""
#             return response.text
#         else:
#             return ""
#     except Exception as e:
#         return ""

def get_twitter_id(screen_name):
    url = f'https://api.twitter.com/1.1/users/lookup.json?screen_name={screen_name}'
    
    # Replace 'REDACTED' with your actual token values
    headers = {
        'Host': 'api.twitter.com',
        'x-csrf-token': ct0,
        'authorization': f"Bearer {bearer}",
        'Cookie': f'ct0={ct0}; auth_token={auth_token};'
    }
    
    response = requests.get(url, headers=headers, verify=False)
    
    if response.status_code == 200:
        response = response.json()[0]
        user_id = response.get('id', None)
        return user_id

    return None

def doesIdMatch(user_id, username):
    if not user_id:
        return False
    results = collection.find_one({"twitter_id": f"{user_id}"})
    if not results:
        return False
    results = list(results['tokens'])

    for result in results:
        twitter_username = result['twitter_username']

        if twitter_username != username:
            return True

    return False

def doesBothMatch(user_id):
    if not user_id:
        return False
    result = collection.find_one({"twitter_id": f"{user_id}"})
    return result != None