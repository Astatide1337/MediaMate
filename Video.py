import tempfile
import shlex
import logging
import random
from typing import Optional
from genericpath import isfile
import re
import subprocess
import os
from Music import GetMusic
from Quote import GetQuote
from datetime import datetime
import textwrap
from PIL import Image, ImageDraw, ImageFont
import easyocr

logging.basicConfig(level=logging.INFO)
reader = easyocr.Reader(["en"])


def CleanFilename(filename):
    """Remove or replace characters that are not allowed in file names."""
    return re.sub(r'[<>:"/\\|?*]', "", filename)


def FormatQuote(quote: str) -> list:
    """
    Formats the quote into lines based on these rules:
    1. Each line must have a maximum of 40 characters or a maximum of 7 spaces between words.
    2. If the line has fewer than 40 characters, add spaces at the beginning and end to make it exactly 40 characters.
    """
    words = quote.split()
    lines = []
    spaces = 0
    line = ""
    for word in words:
        if line:
            line += " "

        line += word
        spaces += 1
        if spaces % 7 == 0 or len(line) >= 35:
            line = line.center(40, " ")
            line += "\n"
            lines.append(line)
            line = ""
            spaces = 0

    if line not in lines:
        line = line.center(40, " ")
        lines.append(line)

    return lines


def TemplateVideo(quote: str, template_file: str, font_path: str):
    """
    Creates a video by overlaying text onto the template video, calculating offsets separately for each line.

    Parameters:
        quote (str): The text to overlay on the video.
        template_file (str): Path to the template video file.
    """
    try:
        # Validate inputs
        if not os.path.isfile(template_file):
            raise FileNotFoundError(f"Template video not found: {template_file}")
        if not template_file.lower().endswith((".mp4", ".mkv", ".avi")):
            raise ValueError(
                "Template file must be a valid video format (e.g., .mp4, .mkv, .avi)."
            )

        # Path to font file
        if not os.path.isfile(font_path):
            raise FileNotFoundError(f"Font file not found: {font_path}")

        # Format the quote
        lines = FormatQuote(quote)

        # Constants for text rendering
        space_width = 1.1  # Approximate width of a space character in pixels
        line_height = 20  # Line height in pixels
        base_y = 100  # Initial vertical position

        # Generate drawtext filters for each line
        drawtext_filters = []
        for i, line in enumerate(lines):

            # Calculate leading spaces and corresponding x-offset
            line = line.center(40).replace("'", "")
            leading_spaces = len(re.match(r"^\s*", line).group(0))
            additional_x_offset = leading_spaces * space_width

            # Calculate vertical position for the line
            y_position = base_y + (i * line_height)

            # Add drawtext filter for the current line
            drawtext_filters.append(
                f"drawtext=fontfile={font_path}:text='{line}':"
                "fontcolor=black:fontsize=20:"
                f"x=((w-text_w)/2)+{additional_x_offset}:y={y_position}"
            )

        # Combine all drawtext filters
        combined_filters = ",".join(drawtext_filters)

        # Sanitize the output file name
        sanitized_quote = CleanFilename(quote)
        output_video = os.path.join(".", "Videos", f"{sanitized_quote}_video.mp4")

        # Construct and execute the FFmpeg command
        command = [
            "ffmpeg",
            "-i",
            template_file,
            "-vf",
            combined_filters,
            "-codec:a",
            "copy",
            "-y",  # Overwrite output file if it exists
            "-loglevel",
            "error",
            output_video,
        ]

        logging.info(f"Executing ffmpeg command: {' '.join(command)}")
        subprocess.run(command, check=True)
        logging.info(f"Video created successfully: {output_video}")

    except subprocess.CalledProcessError as e:
        logging.error(f"FFmpeg error: {e}")
    except FileNotFoundError as e:
        logging.error(f"File not found: {e}")
    except ValueError as e:
        logging.error(f"Validation error: {e}")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")


def PictureVideo(image_path, music_start, music_end, MUSICURL, quote, font_path):
    """
    Creates a video from an image, handling both text and no-text images.

    Parameters:
        image_path (str): Path to the image file.
        music_start (str): Start time for the music in HH:MM:SS or MM:SS format.
        music_end (str): End time for the music in HH:MM:SS or MM:SS format.
        MUSICURL (str): URL of the music to fetch using GetMusic().
        quote (str): Text to overlay on the image.
        font_path (str): Path to the font file for the quote.
    """
    try:
        # Validate the image file
        if not os.path.isfile(image_path):
            raise FileNotFoundError(f"Image not found: {image_path}")

        # Validate music times
        ValidateTimeFormat(music_start)
        ValidateTimeFormat(music_end)

        # Get Music and duration
        duration = GetMusic(MUSICURL, music_start, music_end)

        # Find the generated music file
        music_file = next((f for f in os.listdir(".") if f.endswith(".mp3")), None)
        if not music_file:
            raise FileNotFoundError("Music file not found after GetMusic execution.")

        # Check if the image already has text or not

        imageTEXT = reader.readtext(image_path)

        modified_image_path = image_path  # Default to original image
        if not imageTEXT:
            with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as temp_file:
                modified_image_path = temp_file.name

            quote = quote or GetQuote()
            OverlayQuote(image_path, quote, modified_image_path, font_path)

        # Generate the video with ffmpeg
        output_dir = "./Videos"
        os.makedirs(output_dir, exist_ok=True)
        output_video = f"{output_dir}/{os.path.splitext(os.path.basename(image_path))[0]}_video.mp4"
        command = [
            "ffmpeg",
            "-loop",
            "1",  # Loop the image
            "-i",
            modified_image_path,  # Input (possibly modified) image
            "-i",
            music_file,  # Input music
            "-c:v",
            "libx264",  # Video codec
            "-t",
            str(duration),  # Video duration
            "-pix_fmt",
            "yuvj420p",  # Pixel format for compatibility
            "-loglevel",
            "error",  # Only logs errors
            "-y",  # Overwrites if file already exists
            output_video,  # Output video
        ]

        logging.info(f"Executing ffmpeg command: {' '.join(command)}")
        with subprocess.Popen(command) as process:
            try:
                process.wait()
            except subprocess.CalledProcessError as e:
                logging.error(f"FFmpeg error: {e}")
        logging.info(f"Video created successfully: {output_video}")

        # Clean up temporary files
        if modified_image_path != image_path:
            os.remove(modified_image_path)
        os.remove(music_file)

    except subprocess.CalledProcessError as e:
        logging.error(f"FFmpeg error: {e}")
    except FileNotFoundError as e:
        logging.error(f"File error: {e}")
    except ValueError as e:
        logging.error(f"Validation error: {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")


def OverlayQuote(image_path: str, quote: str, output_path: str, font_path: str) -> None:
    """
    Overlays a quote onto an image and saves it to a new file.

    Parameters:
        image_path (str): Path to the original image.
        quote (str): The quote to overlay on the image.
        output_path (str): Path to save the modified image.
        font_path (str): Path to the font file used for rendering the text.
    """
    try:
        # Load the image
        with Image.open(image_path) as image:
            draw = ImageDraw.Draw(image)

            # Define font and text properties
            if not isfile(font_path):
                raise FileNotFoundError(f"Font file not found: {font_path}")

            font = ImageFont.truetype(font_path, size=64)
            text_color = "white"

            # Calculate the maximum width for the text
            image_width, image_height = image.size
            max_text_width = image_width - 56  # Leave some padding on both sides
            # Estimate the maximum number of characters per line
            avg_char_width = draw.textlength(
                "A", font=font
            )  # Average width of a character
            max_chars_per_line = max_text_width // avg_char_width

            # Wrap the quote text
            wrapped_quote = textwrap.wrap(quote, width=max_chars_per_line)

            # Calculate initial text position (centered vertically)
            total_text_height = sum(
                draw.textbbox((0, 0), line, font=font)[3]
                - draw.textbbox((0, 0), line, font=font)[1]
                for line in wrapped_quote
            )
            total_text_height += (len(wrapped_quote) - 1) * 20  # Add gap between lines
            y = (image_height - total_text_height) / 2

            # Draw each line of text with a gap
            for line in wrapped_quote:
                text_bbox = draw.textbbox((0, 0), line, font=font)
                text_width = text_bbox[2] - text_bbox[0]
                x = (image_width - text_width) / 2
                draw.text((x, y), line, fill=text_color, font=font)
                y += (
                    text_bbox[3] - text_bbox[1] + 20
                )  # Move y position down by line height plus gap

            # Save the modified image
            image.save(output_path)
            logging.info(f"Modified image saved to: {output_path}")

    except Exception as e:
        logging.exception(f"Error overlaying quote on image: {e}")
        raise


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


def ValidateTimeFormat(time_str: str) -> None:
    """
    Validates the format of a given time string.

    The function checks if the input string matches either the "HH:MM:SS" or "MM:SS" format.
    Raises a ValueError if the format is invalid.

    :param time_str: A string representing time in "HH:MM:SS" or "MM:SS" format.
    :raises ValueError: If the time string does not match the expected formats.
    """
    try:
        datetime.strptime(time_str, "%H:%M:%S" if time_str.count(":") == 2 else "%M:%S")
    except ValueError:
        logging.error(f"Invalid time format: {time_str}")
        raise ValueError(f"Invalid time format: {time_str}")


def RandomFile(directory: str) -> Optional[str]:
    """
    Chooses a random file from the specified directory.

    Parameters:
        directory (str): Path to the directory.

    Returns:
        str: The full path of the randomly chosen file.
    """
    try:
        # Check if the directory exists
        if not os.path.isdir(directory):
            raise FileNotFoundError(f"Directory not found: {directory}")

        # Get a list of all files in the directory
        files = [f for f in os.listdir(directory) if isfile(os.path.join(directory, f))]
        if not files:
            raise FileNotFoundError(f"No files found in the directory: {directory}")

        # Choose a random file
        random_file = random.choice(files)
        return os.path.join(directory, random_file)

    except Exception as e:
        logging.error(f"Error: {e}")


# PictureVideo(RandomFile("./Pictures/No-Text"), "0:25", "0:50", "https://www.youtube.com/watch?v=A8ze_f2RqwM&list=RDMMJF-enLzZiqs&index=11")
# TemplateVideo(GetQuote(), RandomFile("./Templates/"))
# FormatQuote('How I felt when bro said "one of your siblings will see all the funerals, one will see none and one wont have any of you at theirs"')
