import tkinter as tk
from tkinter import messagebox, ttk, filedialog
import requests
from PIL import Image, ImageTk
import io
import os

from pytubefix import YouTube  # ensure pytubefix is installed

yt_title = ""
thumbnail_photo = None  # Global variable to hold the thumbnail image
audio_streams = []

def seconds_to_hms(seconds):
    """Convert seconds to an MM:SS format, unless hours exist then HH:MM:SS."""
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h:02}:{m:02}:{s:02}" if h > 0 else f"{m:02}:{s:02}"

def shorten_file_size(_bytes):
    unit = "B"
    if _bytes >= 1024:
        _bytes /= 1024
        unit = "KB"
    if _bytes >= 1024:
        _bytes /= 1024
        unit = "MB"
    if _bytes >= 1024:
        _bytes /= 1024
        unit = "GB"
    return f"{_bytes:.2f} {unit}"

def progress_func(_stream, chunk, bytes_remaining):
    """Callback function to update the progress bar during download."""
    total_size = _stream.filesize
    bytes_downloaded = total_size - bytes_remaining
    percentage = (bytes_downloaded / total_size) * 100
    progress_var.set(percentage)
    progress_bar.update_idletasks()

def search_video():
    global yt_title, thumbnail_photo, audio_streams

    url = url_entry.get().strip()
    if not url:
        messagebox.showerror("Error", "Please enter a YouTube URL")
        return

    try:
        yt = YouTube(url, on_progress_callback=progress_func)
    except Exception as e:
        messagebox.showerror("Error", f"Failed to load video:\n{e}")
        return

    # Fetch and display the thumbnail
    try:
        response = requests.get(yt.thumbnail_url)
        image = Image.open(io.BytesIO(response.content))
        image = image.resize((600, 450))
        image = image.crop((0, 0, 600, 336))  # Crop to maintain aspect ratio

        thumbnail_photo = ImageTk.PhotoImage(image)
        thumbnail_label.config(image=thumbnail_photo)
        thumbnail_label.image = thumbnail_photo  # Keep reference
    except Exception as e:
        print("Error loading thumbnail:", e)
        thumbnail_label.config(text="Thumbnail not available")

    audio_streams = yt.streams.filter(only_audio=True).order_by('bitrate').desc()

    yt_title = yt.title
    duration = seconds_to_hms(yt.length) if yt.length else "N/A"

    info_text = (
        f"Audio: {yt.title}.mp3\n"
        f"Artist: {yt.author}\n"
        f"Length: {duration}\n"
        f"Size: {shorten_file_size(audio_streams[0].filesize)}"
    )
    info_label.config(text=info_text)

def download_stream():
    search_video()

    progress_var.set(0)

    safe_title = yt_title.replace(" ", "_")

    _stream = audio_streams[0]
    bitrate = _stream.abr if hasattr(_stream, 'abr') and _stream.abr else "unknown"
    default_name = f"{safe_title}_{bitrate}"
    def_ext = "mp3"
    filetypes = [("MP3 files", "*.mp3")]

    filename = filedialog.asksaveasfilename(
        title="Save File As",
        initialfile=default_name,
        defaultextension=f".{def_ext}",
        filetypes=filetypes
    )
    if not filename:
        return

    try:
        folder = os.path.dirname(filename)
        file_name = os.path.basename(filename)
        _stream.download(output_path=folder, filename=file_name)
        progress_var.set(100)
        messagebox.showinfo("Success", "Download completed successfully!")
    except Exception as e:
        messagebox.showerror("Error", f"Download failed:\n{e}")

# Setup main window
root = tk.Tk()
root.title("Youtwub Music")
try:
    root.iconbitmap("app.ico")
except Exception as e:
    print("Error setting icon:", e)

progress_var = tk.DoubleVar(root)

top_frame = ttk.Frame(root)
top_frame.grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky="ew")

url_label = ttk.Label(top_frame, text="Enter YouTube URL")
url_label.grid(row=0, column=0, padx=5, pady=5)

url_entry = ttk.Entry(top_frame, width=65)
url_entry.grid(row=0, column=1, padx=5, pady=5)
url_entry.focus_set()  # Focus on the URL entry when the app starts

download_button = ttk.Button(top_frame, text="Download", command=download_stream)
download_button.grid(row=0, column=2, padx=5, pady=5)

url_entry.bind("<Return>", lambda event: download_button.invoke())  # Trigger download on Enter key

thumbnail_label = ttk.Label(root)
thumbnail_label.grid(row=1, column=0, columnspan=2, padx=10, pady=5, sticky="w")

info_label = ttk.Label(root, text="", justify="left")
info_label.grid(row=2, column=0, columnspan=2, padx=10, pady=5, sticky="w")

progress_bar = ttk.Progressbar(root, variable=progress_var, maximum=100)
progress_bar.grid(row=5, column=0, columnspan=2, padx=15, pady=15, sticky="ew")

root.mainloop()
