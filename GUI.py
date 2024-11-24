import logging
import re
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
from Video import TemplateVideo, PictureVideo
from Scraper import ScrapeImages
from Quote import GetQuote
import requests
import sv_ttk
import re

logging.basicConfig(level=logging.INFO)
class MediaMate:
    FONT_PATH = "Roboto-Medium.ttf"
    ENTRY_WIDTH = 50
    PADDING = 5
    def __init__(self, root):
        WINDOW_SIZE = "700x600"
        BACKGROUND_COLOR = "#f0f0f0"

        self.root = root
        self.root.title("MediaMate")
        self.root.geometry(WINDOW_SIZE)
        self.root.configure(bg=BACKGROUND_COLOR)

        # Use ttk for modern themed widgets
        style = ttk.Style()
        style.configure("TButton", padding=6, relief="flat", background="#ccc")
        style.configure("TLabel", background=BACKGROUND_COLOR)
        style.configure("TEntry", padding=5)

        # Create a notebook for tabbed interface
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(padx=10, pady=10, fill="both", expand=True)

        # Video generation tab
        self.video_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.video_frame, text="Template")
        self.create_video_generation_tab()

        # Picture video generation tab
        self.picture_video_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.picture_video_frame, text="Picture")
        self.create_picture_video_tab()

        # Image scraping tab
        self.scrape_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.scrape_frame, text="Scrape")
        self.create_scraping_tab()

        # Configuration tab
        self.config_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.config_frame, text="Config")
        self.create_config_tab()

        # Ensure default font is available
        try:
            self.ensure_default_font()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to ensure default font: {e}")

    

    def create_video_generation_tab(self):
        self.create_label(self.video_frame, "Quote:", 0, 0)
        self.video_quote_entry = self.create_entry(self.video_frame, self.ENTRY_WIDTH, 0, 1)
        self.video_quote_entry.bind("<Enter>", lambda e: self.show_tooltip(e, "Enter a quote for the video."))
        self.video_quote_entry.bind("<KeyRelease>", self.toggle_generate_button)

        self.create_label(self.video_frame, "Template File:", 1, 0)
        self.template_file_entry = self.create_entry(self.video_frame, self.ENTRY_WIDTH, 1, 1)
        self.template_file_entry.bind("<Enter>", lambda e: self.show_tooltip(e, "Select a video template file."))
        self.template_file_entry.bind("<KeyRelease>", self.toggle_generate_button)

        self.create_button(self.video_frame, "Browse", self.browse_template_file, 1, 2)

        self.generate_button = self.create_button(self.video_frame, "Generate", self.generate_video, 2, 1)
        self.generate_button.state(["disabled"])

    def create_button(self, parent, text, command, row, column):
        button = ttk.Button(parent, text=text, command=command)
        button.grid(row=row, column=column, padx=self.PADDING, pady=self.PADDING)
        return button

    def show_tooltip(self, event: tk.Event, text: str, duration: int = 1500) -> None:
        """Display a tooltip with the given text at the event location."""
        try:
            if hasattr(self, '_tooltip') and self._tooltip:
                self._tooltip.destroy()
                self._tooltip = None
            self._tooltip = tk.Toplevel(self.root)
            self._tooltip.wm_overrideredirect(True)
            self._tooltip.geometry(f"+{event.x_root + 10}+{event.y_root + 10}")
            label = ttk.Label(self._tooltip, text=text, background="black", relief="solid", borderwidth=1)
            label.pack(ipadx=5, ipady=5)
            self._tooltip.after(duration, lambda: (self._tooltip.destroy(), setattr(self, '_tooltip', None)))  # Tooltip disappears after the specified duration
        except Exception as e:
            messagebox.showerror("Error", f"Failed to show tooltip: {e}")

    def toggle_generate_button(self, event):
        if self.video_quote_entry.get() and self.template_file_entry.get():
            self.generate_button.state(["!disabled"])
        else:
            self.generate_button.state(["disabled"])

    def browse_template_file(self):
        try:
            file_path = filedialog.askopenfilename(filetypes=[("Video Files", "*.mp4 *.mkv *.avi")])
            if file_path:
                self.template_file_entry.delete(0, tk.END)
                self.template_file_entry.insert(0, file_path)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to browse template file: {e}")

    def generate_video(self):
        quote = self.video_quote_entry.get() or self.default_quote_entry.get()
        template_file = self.template_file_entry.get()
        font_path = self.FONT_PATH

        if not template_file:
            messagebox.showerror("Error", "Please provide a template file.")
            return

        if not quote:
            try:
                TemplateVideo(GetQuote(), template_file, font_path)
                messagebox.showinfo("Success", "Video generated successfully.")
            except Exception as e:
                self.handle_error("generate video", e)
        else:
            try:
                TemplateVideo(quote, template_file, font_path)
                messagebox.showinfo("Success", "Video generated successfully.")
            except Exception as e:
                self.handle_error("generate video", e)

    def create_picture_video_tab(self):
        ENTRY_WIDTH_LARGE = 50
        ENTRY_WIDTH_SMALL = 20

        self.create_label(self.picture_video_frame, "Image Path:", 0, 0)
        self.image_path_entry = self.create_entry(self.picture_video_frame, ENTRY_WIDTH_LARGE, 0, 1)
        self.image_path_entry.bind("<Enter>", lambda e: self.show_tooltip(e, "Select an image file for the video."))
        self.create_button(self.picture_video_frame, "Browse", self.browse_image_file, 0, 2)

        self.create_label(self.picture_video_frame, "Music Start:", 1, 0)
        self.music_start_entry = self.create_entry(self.picture_video_frame, ENTRY_WIDTH_SMALL, 1, 1)
        self.music_start_entry.bind("<Enter>", lambda e: self.show_tooltip(e, "Enter music start time in HH:MM:SS or MM:SS format."))

        self.create_label(self.picture_video_frame, "Music End:", 2, 0)
        self.music_end_entry = self.create_entry(self.picture_video_frame, ENTRY_WIDTH_SMALL, 2, 1)
        self.music_end_entry.bind("<Enter>", lambda e: self.show_tooltip(e, "Enter music end time in HH:MM:SS or MM:SS format."))

        self.create_label(self.picture_video_frame, "Music URL:", 3, 0)
        self.music_url_entry = self.create_entry(self.picture_video_frame, ENTRY_WIDTH_LARGE, 3, 1)
        self.music_url_entry.bind("<Enter>", lambda e: self.show_tooltip(e, "Enter the URL for the music track."))

        self.create_button(self.picture_video_frame, "Generate Picture Video", self.generate_picture_video, 4, 1)

    def create_scraping_tab(self):
        self.create_label(self.scrape_frame, "URL:", 0, 0)
        self.url_entry = self.create_entry(self.scrape_frame, 50, 0, 1)
        self.url_entry.insert(0, "Enter the URL to scrape images from")

        self.create_label(self.scrape_frame, "Save Folder:", 1, 0)
        self.folder_entry = self.create_entry(self.scrape_frame, 50, 1, 1)
        self.create_button(self.scrape_frame, "Browse", self.browse_folder, 1, 2)

        self.create_label(self.scrape_frame, "Scroll Times:", 2, 0)
        self.scroll_times_entry = self.create_entry(self.scrape_frame, 10, 2, 1)
        self.scroll_times_entry.insert(0, "Enter number of scrolls")

        self.create_button(self.scrape_frame, "Scrape Images", self.scrape_images, 3, 1)

    def create_config_tab(self):
        if not hasattr(self, 'config_tab_created'):
            ENTRY_WIDTH = 50  # Constant for entry width

            self.create_label(self.config_frame, "Default Quote:", 0, 0)
            self.default_quote_entry = self.create_entry(self.config_frame, ENTRY_WIDTH, 0, 1)
            self.default_quote_entry.bind("<Enter>", lambda e: self.show_tooltip(e, "Enter the default quote to be used."))

            self.create_label(self.config_frame, "Default Font:", 1, 0)
            self.default_font_entry = self.create_entry(self.config_frame, ENTRY_WIDTH, 1, 1)
            self.default_font_entry.bind("<Enter>", lambda e: self.show_tooltip(e, "Select the default font file."))
            ttk.Button(self.config_frame, text="Browse", command=self.browse_font_file).grid(row=1, column=2, padx=5, pady=5)

            self.config_tab_created = True

    def validate_url(self, url):
        try:
            # Validate the URL format using a regular expression
            return re.match(r'^(http|https)://', url) is not None
        except Exception as e:
            # Handle exceptions that may occur during URL validation
            messagebox.showerror("Error", f"URL validation failed: {e}")
            return False
    def create_label(self, parent, text, row, column):
        label = ttk.Label(parent, text=text)
        label.grid(row=row, column=column, sticky="w", padx=5, pady=5)
        return label

    def create_entry(self, parent, width, row, column):
        entry = ttk.Entry(parent, width=width)
        entry.grid(row=row, column=column, padx=5, pady=5)
        return entry

    def browse_template_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Video Files", "*.mp4 *.mkv *.avi")])
        if file_path:
            self.template_file_entry.delete(0, tk.END)
            self.template_file_entry.insert(0, file_path)

    def browse_image_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.jpg *.jpeg *.png")])
        if file_path:
            self.image_path_entry.delete(0, tk.END)
            self.image_path_entry.insert(0, file_path)

    def browse_folder(self):
        folder_path = filedialog.askdirectory()
        if folder_path:
            self.folder_entry.delete(0, tk.END)
            self.folder_entry.insert(0, folder_path)

    def browse_font_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Font Files", "*.ttf")])
        if file_path:
            self.default_font_entry.delete(0, tk.END)
            self.default_font_entry.insert(0, file_path)

    def ensure_default_font(self):
        if not os.path.isfile(self.FONT_PATH):
            try:
                url = "https://github.com/openmaptiles/fonts/raw/refs/heads/master/roboto/Roboto-Medium.ttf"
                response = requests.get(url)
                with open(self.FONT_PATH, 'wb') as f:
                    f.write(response.content)
                messagebox.showinfo("Info", "Default font downloaded successfully.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to download default font: {e}")

    def handle_error(self, action, e):
        messagebox.showerror("Error", f"Failed to {action}: {e}")

    def generate_video(self):
        quote = self.video_quote_entry.get() or self.default_quote_entry.get()
        template_file = self.template_file_entry.get()
        font_path = self.FONT_PATH

        if not template_file:
            messagebox.showerror("Error", "Please provide a template file.")
            return

        if not quote:
            try:
                TemplateVideo(GetQuote(), template_file, font_path)
                messagebox.showinfo("Success", "Video generated successfully.")
            except Exception as e:
                self.handle_error("generate video", e)
        else:
            try:
                TemplateVideo(quote, template_file, font_path)
                messagebox.showinfo("Success", "Video generated successfully.")
            except Exception as e:
                self.handle_error("generate video", e)

    def generate_picture_video(self):
        image_path = self.image_path_entry.get()
        music_start = self.music_start_entry.get()
        music_end = self.music_end_entry.get()
        music_url = self.music_url_entry.get()
        quote = self.default_quote_entry.get()
        font_path = self.default_font_entry.get() or self.FONT_PATH

        if not image_path or not music_start or not music_end or not music_url:
            messagebox.showerror("Error", "Please provide all required inputs for Picture Video.")
            return

        if not re.match(r"^\d{1,2}:\d{2}(:\d{2})?$", music_start) or not re.match(r"^\d{1,2}:\d{2}(:\d{2})?$", music_end):
            messagebox.showerror("Error", "Music start and end times must be in HH:MM:SS or MM:SS format.")
            return

        try:
            PictureVideo(image_path, music_start, music_end, music_url, quote, font_path)
            messagebox.showinfo("Success", "Picture video generated successfully.")
        except Exception as e:
            self.handle_error("generate picture video", e)

    def scrape_images(self):
        url = self.url_entry.get()
        folder = self.folder_entry.get()
        scroll_times = self.scroll_times_entry.get()
        logging.info("Starting image scraping process.")

        if not self.validate_url(url):
            messagebox.showerror("Error", "Invalid URL format.")
            return

        if not os.path.isdir(folder) or not os.access(folder, os.W_OK):
            messagebox.showerror("Error", "Invalid or unwritable folder path.")
            return

        if not url or not folder or not scroll_times.isdigit():
            messagebox.showerror("Error", "Please provide a valid URL, folder, and scroll times.")
            return

        try:
            scroll_times_int = int(scroll_times)
        except ValueError:
            messagebox.showerror("Error", "Scroll times must be a valid integer.")
            return

        try:
            ScrapeImages(url, folder, scroll_times_int)
            messagebox.showinfo("Success", "Images scraped successfully.")
            logging.info("Image scraping process completed successfully.")
        except Exception as e:
            self.handle_error("scrape images", e)
            logging.error(f"Image scraping process failed: {e}")

# Example usage
if __name__ == "__main__":
    root = tk.Tk()
    app = MediaMate(root)
    sv_ttk.set_theme("dark")
    root.mainloop()