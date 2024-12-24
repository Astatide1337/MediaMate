import logging
import subprocess
from bs4 import BeautifulSoup
import random
import requests
from typing import Dict, List, Optional
import os
from TTS.api import TTS
import torch
import tempfile
import shutil



def GenerateTTS(text: str, speaker: str, filename: str):
    device = "cuda" if torch.cuda.is_available() else "cpu"

    tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(device)

    tts.tts_to_file(
    text=text,
    speaker_wav=f"{speaker}",
    language="en",
    file_path=filename
    )


def DownloadVoice(URL: str, Name: str) -> None:
    try:
        temp_dir = tempfile.mkdtemp()
        temp_file = os.path.join(temp_dir, f"{Name}.wav")

        options = [
            "yt-dlp",
            "-f",
            "251",
            "-x",
            "--audio-format",
            "wav",
            "--output",
            temp_file,
            URL,
        ]

        subprocess.run(options, check=True)

        shutil.move(temp_file, f"./Voices/{Name.replace(' ', '')}.wav")

        logging.info(f"Successfully downloaded: {URL}")

    except subprocess.CalledProcessError as e:
        logging.error(f"An error occurred while downloading {URL}: {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
    finally:
        shutil.rmtree(temp_dir)

#https://www.youtube.com/watch?v=b4lDJe9Nv4k

# DownloadVoice("https://www.youtube.com/watch?v=uk6f9L2XhMo", "Nolan Reads")
# GenerateTTS(
#     """Sometimes he would walk for hours and
#     miles and return only at midnight to his house. And
#     on his way he would see the cottages and homes with
#     their dark windows, and it was not unequal to
#     walking through a graveyard where only the faintest
#     glimmers of firefly light appeared in flickers behind
#     the windows. Sudden gray phantoms seemed to
#     manifest upon inner room walls where a curtain was
#     still undrawn against the night, or there were
#     whisperings and murmurs where a window in a tomblike building was still open
#     """,
#     "NolanReads",
#     "./TTS/Pedestrian.mp3",
# )
#AudibleQuote()
#scrapeWikiquote("albert einstein")