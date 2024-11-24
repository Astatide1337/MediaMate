import requests
import logging
import re

logging.basicConfig(level=logging.INFO)

def GetQuote() -> str:
    """
    Fetches a stoic quote from an API and returns it if the quote is valid.
    A valid quote is not None and has a length of 150 characters or less.
    """
    url = "https://stoic.tekloon.net/stoic-quote"
    while True:
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            json_data = response.json()
            quote = json_data.get("data", {}).get("quote")

            if quote and len(quote) <= 150:
                # Use regex to remove unwanted characters
                return re.sub(r"[^a-zA-Z0-9.,'\s]", "", quote)
            logging.info("Quote Too Long or None, Trying Again")
        except requests.RequestException as e:
            logging.error(f"Request failed: {e}")