import re
from datetime import datetime
import yt_dlp
import logging
import subprocess
import os
import shlex

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def GetDuration(file_path, timeout=None):
    """
    Get the duration of an audio file using ffprobe.

    Parameters:
        file_path (str): Path to the audio file.
        timeout (Optional[float]): Maximum time in seconds to wait for the command to complete.

    Returns:
        float: Duration of the audio file in seconds.
    """
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"The file {file_path} does not exist.")
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                shlex.quote(file_path),
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
            timeout=timeout,
        )
        if result.stdout:
            return float(result.stdout)
        else:
            logging.error("No duration found in the output.")
            raise ValueError("No duration found in the output.")
    except subprocess.CalledProcessError as e:
        logging.exception(f"Error getting audio duration: {e}")
        raise


def ParseTime(time_str: str) -> int:
    """Parse a time string in HH:MM:SS or MM:SS format to seconds."""
    if not isinstance(time_str, str) or not time_str:
        raise ValueError("Input must be a non-empty string")
    try:
        time_obj = datetime.strptime(time_str, "%H:%M:%S")
    except ValueError:
        time_obj = datetime.strptime(time_str, "%M:%S")
    return time_obj.hour * 3600 + time_obj.minute * 60 + time_obj.second


def GetMusic(url: str, start: str, end: str) -> int:
    """
    Downloads a segment of audio from a given URL using yt_dlp and ffmpeg,
    ensuring the segment is within specified start and end times.

    :param url: URL of the music video.
    :param start: Start time in "MM:SS" or "HH:MM:SS" format.
    :param end: End time in "MM:SS" or "HH:MM:SS" format.
    :return: Expected duration of the downloaded audio segment in seconds.
    """
    try:
        # Validate URL
        if not isinstance(url, str) or not url.startswith("http"):
            raise ValueError("Invalid URL provided.")

        # Validate time format
        time_pattern = re.compile(r"^\d{1,2}:\d{2}(:\d{2})?$")
        if not time_pattern.match(start) or not time_pattern.match(end):
            raise ValueError(
                "Start and end times must be in the format MM:SS or HH:MM:SS."
            )

        # Clean URL
        if "&" in url:
            url = url.split("&")[0]
            logging.info(f"Cleaned URL: {url}")

        # Calculate expected duration
        start_seconds = ParseTime(start)
        end_seconds = ParseTime(end)
        if end_seconds <= start_seconds:
            raise ValueError("End time must be greater than start time.")
        expected_duration = end_seconds - start_seconds

        # Set ffmpeg arguments
        ffmpeg_args = {"ffmpeg_i": ["-ss", start, "-to", end]}

        # Set options for yt_dlp
        opts = {
            "external_downloader": "ffmpeg",
            "external_downloader_args": ffmpeg_args,
            "format": "bestaudio/best",
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }
            ],
            "outtmpl": "%(title)s.%(ext)s",
            "quiet": True,
        }

        # Download the music
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])

        # Find the downloaded music file
        music_file = next((f for f in os.listdir(".") if f.endswith(".mp3")), None)
        if not music_file:
            raise FileNotFoundError("Music file not found after download.")

        # Get the actual duration of the downloaded file
        actual_duration = GetDuration(music_file)

        # Compare durations and adjust if necessary
        if actual_duration != expected_duration:
            difference = actual_duration - expected_duration
            if difference > 0:
                # Trim the difference from the beginning of the music file
                trimmed_file = os.path.join(".", f"trimmed_{music_file}")
                with subprocess.Popen(
                    [
                        "ffmpeg",
                        "-i",
                        music_file,
                        "-ss",
                        str(difference),
                        "-t",
                        str(expected_duration),
                        "-c",
                        "copy",
                        trimmed_file,
                        "-y",
                        "-loglevel",
                        "error",
                    ]
                ) as proc:
                    proc.wait()
                os.remove(music_file)
                os.rename(trimmed_file, music_file)

        return expected_duration

    except yt_dlp.utils.DownloadError as e:
        logging.error(f"Download error: {e}")
    except ValueError as e:
        logging.error(f"Value error: {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")


# Example usage
# GetMusic("https://www.youtube.com/watch?v=wl-ymIpl0nI&list=RDJF-enLzZiqs&index=2", "1:00", "1:22")
