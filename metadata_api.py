import requests
import os
from dotenv import load_dotenv
from urlextract import URLExtract

load_dotenv()

MORALIS_API = os.getenv('MORALIS_API')

headers = {
  "Accept": "application/json",
  "X-API-Key": MORALIS_API
}

def get_solana_token_metadata_uri(token_address):
    url = f"https://solana-gateway.moralis.io/token/mainnet/{token_address}/metadata"
    print(url)
    print(headers)
    response = requests.request("GET", url, headers=headers)
    print(response.json())
    
    if response.status_code != 200:
        return 'err404'
    
    response = response.json()
    if not 'metaplex' in response and not 'metadataUri' in response['metaplex']:
        return None

    return response['metaplex']['metadataUri']


def get_twitter_link(token_address):
    metadata_uri = get_solana_token_metadata_uri(token_address)
    if 'err404' in metadata_uri:
        return 'err404'

    if not metadata_uri:
        return None

    response = requests.request("GET", metadata_uri)

    if response.status_code != 200:
        return 'err404'

    response = response.json()
    print(response)
    
    url = response.get('extensions', {}).get('twitter', None)
    
    if url and ("twitter.com" in url or "x.com" in url):
        return url

    description = response.get('description', None)

    extractor = URLExtract()
    urls = extractor.find_urls(description)
    urls = [url for url in urls]
    
    for url in urls:
        if "x.com" in url or "twitter.com" in url:
            return url

    return url