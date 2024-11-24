from PIL import Image
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import requests
import logging
import os
from urllib.parse import urljoin

"""
LINKS = {
    "No-Text": {
        "URLS": ["https://in.pinterest.com/zzzzandrey/_created"]
    },
    "Text": {
        "URLS": ["https://in.pinterest.com/stoicsalpha/_created",]
    }
}
"""
logging.basicConfig(level=logging.INFO)

if not os.path.exists("Pictures"):
    os.makedirs("Pictures")

if not os.path.exists("Videos"):
    os.makedirs("Videos")


def ResizeImages(directory: str) -> None:
    """
    Resizes all image files in the specified directory to 1080x1350 pixels if they are not already that size.

    Parameters:
    directory (str): The path to the directory containing images to be resized.
    """
    if not os.path.isdir(directory):
        logging.error(f"Directory {directory} does not exist.")
        return

    try:
        with os.scandir(directory) as entries:
            for entry in entries:
                if entry.is_file() and entry.name.lower().endswith(
                    (".png", ".jpg", ".jpeg", ".bmp", ".gif", ".tiff")
                ):
                    try:
                        with Image.open(entry.path) as img:
                            if img.size != (1080, 1350):
                                img = img.resize((1080, 1350), Image.LANCZOS)
                                img.save(entry.path)
                                logging.info(f"Resized and saved: {entry.path}")
                            else:
                                logging.info(
                                    f"Image {entry.name} is already 1080x1350, skipping resize."
                                )
                    except Exception as e:
                        logging.error(f"Failed to process image {entry.name}: {e}")
    except OSError as e:
        logging.error(f"Error accessing directory {directory}: {e}")


def DownloadImage(URL: str, folder: str) -> None:
    """
    Downloads an image from a given URL and saves it to the specified folder.

    Parameters:
    URL (str): The URL of the image to be downloaded.
    folder (str): The path to the folder where the image should be saved.
    """
    if not URL.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff")):
        logging.error(f"Invalid image URL: {URL}")
        return
    try:
        with requests.get(URL, stream=True) as response:
            response.raise_for_status()

            # Get the image name from the URL
            IMGNAME = os.path.basename(URL)
            IMGPATH = os.path.join(folder, IMGNAME)

            os.makedirs(folder, exist_ok=True)
            with open(IMGPATH, "wb") as FILE:
                for chunk in response.iter_content(chunk_size=8192):
                    FILE.write(chunk)
            logging.info(f"Saved: {IMGPATH}")

    except requests.RequestException as e:
        logging.error(f"Failed to save image {URL}: {e}")


def ScrapeImages(url: str, folder: str, MAX: int) -> None:
    """Scrape images from a webpage and download those containing '236x' in their URL.

    Args:
        url (str): The URL of the webpage to scrape images from.
        folder (str): The directory path where the images will be saved.
        MAX (int): The number of times the page will be scrolled.
    """
    options = webdriver.ChromeOptions()
    options.add_experimental_option("excludeSwitches", ["enable-logging"])

    try:
        with webdriver.Chrome(options=options) as driver:
            driver.get(url)
            for _ in range(MAX):
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                logging.info("SCROLLING PAGE")
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "img"))
                )

            soup = BeautifulSoup(driver.page_source, "html.parser")
            for IMGTAG in soup.find_all("img", src=True):
                IMGSRC = IMGTAG["src"]
                logging.info(IMGSRC)
                if "236x" in IMGSRC:
                    IMGSRC = IMGSRC.replace("236", "736")
                    DownloadImage(IMGSRC, folder)
    except Exception as e:
        logging.error(f"An error occurred while using the WebDriver: {e}")
