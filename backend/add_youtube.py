"""
add_youtube.py
---------------
YouTube link se seedha terminal ke zariye song add karne ke liye
(bina frontend/website khole).

Chalane ka tareeqa:
    python add_youtube.py "https://youtu.be/XXXXXXXXX"
    python add_youtube.py "https://youtu.be/XXXXXXXXX" "Song Title" "Artist"

Agar title/artist na diya jaye, to YouTube video ke asal
naam/channel se khud utha liya jayega.
"""

import os
import sys
import uuid
import yt_dlp

from add_song import add_song

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def add_from_youtube(youtube_url, title=None, artist=None):
    unique_id = uuid.uuid4().hex
    output_path = os.path.join(UPLOAD_FOLDER, unique_id)

    ydl_options = {
        "format": "bestaudio/best",
        "outtmpl": output_path + ".%(ext)s",
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
        }],
        "quiet": True,
    }

    print("Audio downloading from YouTube...")

    with yt_dlp.YoutubeDL(ydl_options) as ydl:
        video_info = ydl.extract_info(youtube_url, download=True)

    if video_info and "entries" in video_info and video_info["entries"]:
        video_info = video_info["entries"][0]

    fetched_title = video_info.get("title") if video_info else None
    fetched_artist = (video_info.get("uploader") or video_info.get("channel")) if video_info else None

    final_title = title or fetched_title or "Unknown Title"
    final_artist = artist or fetched_artist or "Unknown Artist"

    final_path = output_path + ".mp3"
    song_id = add_song(final_path, final_title, final_artist, source_type="youtube", source_url=youtube_url)

    print(f"'{final_title}' by {final_artist} has been added (Song ID: {song_id})")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print('Usage: python add_youtube.py "youtube_link" ["Title"] ["Artist"]')
    else:
        url = sys.argv[1]
        title_arg = sys.argv[2] if len(sys.argv) > 2 else None
        artist_arg = sys.argv[3] if len(sys.argv) > 3 else None
        add_from_youtube(url, title_arg, artist_arg)