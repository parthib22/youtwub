import tkinter as tk
from tkinter import messagebox, ttk, filedialog
import requests
from PIL import Image, ImageTk
import io
import os
from pytubefix import YouTube  # ensure pytubefix is installed

# Global dictionaries to map listbox indices to stream objects
video_streams_dict = {}
video_only_streams_dict = {}
audio_streams_dict = {}

yt_title = ""
thumbnail_photo = None  # Global variable to hold the thumbnail image

def seconds_to_hms(seconds):
    """Convert seconds to a MM:SS format, unless hours exist then HH:MM:SS."""
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    if h > 0:
        return f"{h:02}:{m:02}:{s:02}"
    else:
        return f"{m:02}:{s:02}"

def shorten_file_size(bytes):
    unit = "B"
    if bytes >= 1024:
        bytes /= 1024
        unit = "KB"
    if bytes >= 1024:
        bytes /= 1024
        unit = "MB"
    if bytes >= 1024:
        bytes /= 1024
        unit = "GB"
    return f"{bytes:.2f} {unit}"

def progress_func(stream, chunk, bytes_remaining):
    """Callback function to update the progress bar during download."""
    total_size = stream.filesize
    bytes_downloaded = total_size - bytes_remaining
    percentage = (bytes_downloaded / total_size) * 100
    progress_var.set(percentage)
    progress_bar.update_idletasks()

def search_video():
    global yt_title, thumbnail_photo
    url = url_entry.get().strip()
    if not url:
        messagebox.showerror("Error", "Please enter a YouTube URL")
        return

    try:
        yt = YouTube(url, on_progress_callback=progress_func)
    except Exception as e:
        messagebox.showerror("Error", f"Failed to load video:\n{e}")
        return

    yt_title = yt.title
    duration = seconds_to_hms(yt.length) if yt.length else "N/A"
    views = yt.views if yt.views else "N/A"
    info_text = (
        f"Video: {yt.title}\n"
        f"Channel: {yt.author}\n"
        f"Duration: {duration}\n"
        f"{views:,} views\n"
    )
    info_label.config(text=info_text)

    # Fetch and display the thumbnail above the info text, aligned to the left.
    thumbnail_url = yt.thumbnail_url
    try:
        response = requests.get(thumbnail_url)
        image_data = response.content
        image = Image.open(io.BytesIO(image_data))

        image = image.resize((600, 450))
        left = (600 - 600) // 2
        top = (450 - 336) // 2
        right = (600 + 600) // 2
        bottom = (450 + 336) // 2
        image = image.crop((left, top, right, bottom))

        thumbnail_photo = ImageTk.PhotoImage(image)
        thumbnail_label.config(image=thumbnail_photo)
        thumbnail_label.image = thumbnail_photo  # keep a reference
    except Exception as e:
        print("Error loading thumbnail:", e)
        thumbnail_label.config(text="Thumbnail not available")

    # Clear listboxes and dictionaries
    video_listbox.delete(0, tk.END)
    video_only_listbox.delete(0, tk.END)
    audio_listbox.delete(0, tk.END)
    video_streams_dict.clear()
    video_only_streams_dict.clear()
    audio_streams_dict.clear()
    progress_var.set(0)

    progressive_streams = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc()
    video_only_streams = yt.streams.filter(only_video=True, file_extension='mp4').order_by('resolution').desc()
    audio_streams = yt.streams.filter(only_audio=True).order_by('bitrate').desc()

    for idx, stream in enumerate(progressive_streams):
        info = f"{stream.resolution} - {stream.fps}fps - {shorten_file_size(stream.filesize)}"
        video_listbox.insert(tk.END, info)
        video_streams_dict[idx] = stream

    for idx, stream in enumerate(video_only_streams):
        info = f"{stream.resolution} - {stream.fps}fps - {shorten_file_size(stream.filesize)}"
        video_only_listbox.insert(tk.END, info)
        video_only_streams_dict[idx] = stream

    for idx, stream in enumerate(audio_streams):
        abr = stream.abr if hasattr(stream, 'abr') and stream.abr else "N/A"
        info = f"{abr} - {shorten_file_size(stream.filesize)}"
        audio_listbox.insert(tk.END, info)
        audio_streams_dict[idx] = stream

def download_stream():
    video_sel = video_listbox.curselection()
    audio_sel = audio_listbox.curselection()
    video_only_sel = video_only_listbox.curselection()

    selections = [bool(video_sel), bool(audio_sel), bool(video_only_sel)]

    if sum(selections) != 1:
        messagebox.showerror("Error", "Please select only one stream from one of the lists")
        return

    safe_title = yt_title.replace(" ", "_")

    if video_sel:
        idx = video_sel[0]
        stream = video_streams_dict.get(idx)
        stream_type = stream.mime_type.split('/')[0]
        resolution = stream.resolution if stream.resolution else "unknown"
        default_name = f"{safe_title}_{stream_type}_{resolution}"
        def_ext = "mp4"
        filetypes = [("MP4 files", "*.mp4")]
    elif audio_sel:
        idx = audio_sel[0]
        stream = audio_streams_dict.get(idx)
        stream_type = stream.mime_type.split('/')[0]
        bitrate = stream.abr if hasattr(stream, 'abr') and stream.abr else "unknown"
        default_name = f"{safe_title}_{stream_type}_{bitrate}"
        def_ext = "mp3"
        filetypes = [("MP3 files", "*.mp3"), ("M4A files", "*.m4a")]
    elif video_only_sel:
        idx = video_only_sel[0]
        stream = video_only_streams_dict.get(idx)
        stream_type = stream.mime_type.split('/')[0]
        resolution = stream.resolution if stream.resolution else "unknown"
        default_name = f"{safe_title}_{stream_type}_{resolution}"
        def_ext = "mp4"
        filetypes = [("MP4 files", "*.mp4")]

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
        progress_var.set(0)
        stream.download(output_path=folder, filename=file_name)
        messagebox.showinfo("Success", "Download completed successfully!")
    except Exception as e:
        messagebox.showerror("Error", f"Download failed:\n{e}")

# Setup main window and create the progress variable after the root is created
root = tk.Tk()
root.title("YouTube Downloader")
try:
    root.iconbitmap("app.ico")
except Exception as e:
    print("Error setting icon:", e)

# Create the progress variable now that the root exists
progress_var = tk.DoubleVar(root)

top_frame = ttk.Frame(root)
top_frame.grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky="ew")

url_label = ttk.Label(top_frame, text="Enter YouTube URL")
url_label.grid(row=0, column=0, padx=5, pady=5)

url_entry = ttk.Entry(top_frame, width=65)
url_entry.grid(row=0, column=1, padx=5, pady=5)

search_button = ttk.Button(top_frame, text="Search", command=search_video)
search_button.grid(row=0, column=2, padx=5, pady=5)

thumbnail_label = ttk.Label(root)
thumbnail_label.grid(row=1, column=0, columnspan=2, padx=10, pady=5, sticky="w")

info_label = ttk.Label(root, text="", justify="left")
info_label.grid(row=2, column=0, columnspan=2, padx=10, pady=5, sticky="w")

listboxes_frame = ttk.Frame(root)
listboxes_frame.grid(row=3, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")

# Video Only Streams Section
video_only_frame = ttk.Frame(listboxes_frame)
video_only_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
video_only_label = ttk.Label(video_only_frame, text="Video Only")
video_only_label.pack(anchor="w")
video_only_listbox = tk.Listbox(video_only_frame, width=32, height=10, selectmode=tk.SINGLE)
video_only_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

# Audio Only Section
audio_frame = ttk.Frame(listboxes_frame)
audio_frame.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")
audio_label = ttk.Label(audio_frame, text="Audio Only")
audio_label.pack(anchor="w")
audio_listbox = tk.Listbox(audio_frame, width=31, height=10, selectmode=tk.SINGLE)
audio_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

# Video + Audio Section
video_frame = ttk.Frame(listboxes_frame)
video_frame.grid(row=0, column=2, padx=5, pady=5, sticky="nsew")
video_label = ttk.Label(video_frame, text="Video + Audio")
video_label.pack(anchor="w")
video_listbox = tk.Listbox(video_frame, width=31, height=10, selectmode=tk.SINGLE)
video_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

download_button = ttk.Button(root, text="Download", command=download_stream)
download_button.grid(row=4, column=0, columnspan=2, padx=10, pady=10)

progress_bar = ttk.Progressbar(root, variable=progress_var, maximum=100)
progress_bar.grid(row=5, column=0, columnspan=2, padx=15, pady=15, sticky="ew")

root.mainloop()
