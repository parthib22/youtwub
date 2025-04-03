from pytubefix import YouTube
from pytubefix.cli import on_progress

url = "https://www.youtube.com/watch?v=Wcd6r97fOgo"

yt = YouTube(url, on_progress_callback=on_progress)
print(yt.title)
for y in yt.streams:
    print(f'{y} : {y.url}')

# ys = yt.streams.get_highest_resolution()
# ys.download()