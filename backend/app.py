"""
app.py
------
Ye Flask server hai - iska kaam hai humare Python functions
(database.py, add_song.py, identify.py) ko HTTP API ke roop mein
expose karna, taake React frontend inhe call kar sake.

4 endpoints hain:
  GET  /songs/count       -> abhi kitne songs hain, aur max limit kya hai
  POST /add-song          -> file upload karke song add karna
  POST /add-song-youtube  -> YouTube link se song add karna
  POST /identify          -> recorded clip se song pehchanna
"""

import os
import uuid
from flask import Flask, request, jsonify
from flask_cors import CORS

from add_song import add_song, get_song_count, MAX_SONGS
from identify import identify_song

app = Flask(__name__)

# CORS zaroori hai kyunke React (jaise localhost:3000 par) aur
# Flask (localhost:5000 par) alag "origins" par chalte hain.
# Bina CORS ke, browser security ki wajah se request block kar dega.
CORS(app)

# Uploaded aur recorded audio files yahan save hongi
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# ---------- Endpoint 1: Total songs count ----------
@app.route("/songs/count", methods=["GET"])
def songs_count():
    """
    Frontend ka counter ("50 / 1000 Songs") isi endpoint se
    apna data lega.
    """
    current_count = get_song_count()
    return jsonify({
        "count": current_count,
        "max": MAX_SONGS,
        "remaining": MAX_SONGS - current_count
    })


# ---------- Endpoint 2: File upload se song add karna ----------
@app.route("/add-song", methods=["POST"])
def add_song_endpoint():
    """
    Frontend se ek audio file (multipart/form-data) aayegi,
    sath mein title aur artist bhi (form fields ke roop mein).
    """

    # request.files us jagah hai jahan uploaded files milti hain
    if "file" not in request.files:
        return jsonify({"error": "Koi file upload nahi hui"}), 400

    uploaded_file = request.files["file"]
    title = request.form.get("title", "Unknown Title")
    artist = request.form.get("artist", "Unknown Artist")

    # File ko ek unique naam de kar save karna - taake do users
    # agar same naam ki file upload karein to overwrite na ho
    unique_filename = f"{uuid.uuid4().hex}_{uploaded_file.filename}"
    file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
    uploaded_file.save(file_path)

    try:
        song_id = add_song(file_path, title, artist, source_type="upload")
        return jsonify({
            "success": True,
            "song_id": song_id,
            "title": title,
            "artist": artist
        })
    except Exception as e:
        # Agar limit poori ho chuki ho, ya koi aur error aaye,
        # to frontend ko saaf error message milega
        return jsonify({"error": str(e)}), 400


# ---------- Endpoint 3: YouTube link se song add karna ----------
@app.route("/add-song-youtube", methods=["POST"])
def add_song_youtube_endpoint():
    """
    Frontend se JSON body aayegi: { "url": "...", "title": "...", "artist": "..." }
    Hum yt-dlp se us link ka audio nikaal kar MP3 banayenge,
    phir usay wahi add_song() function ko de denge.
    """
    import yt_dlp

    data = request.get_json()
    youtube_url = data.get("url")
    title = data.get("title", "Unknown Title")
    artist = data.get("artist", "Unknown Artist")

    if not youtube_url:
        return jsonify({"error": "YouTube link nahi diya gaya"}), 400

    unique_id = uuid.uuid4().hex
    output_path = os.path.join(UPLOAD_FOLDER, unique_id)

    # yt-dlp ki settings: sirf audio nikaalo, MP3 mein convert karo
    ydl_options = {
        "format": "bestaudio/best",
        "outtmpl": output_path + ".%(ext)s",
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
        }],
        "quiet": True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_options) as ydl:
            ydl.download([youtube_url])

        final_path = output_path + ".mp3"
        song_id = add_song(final_path, title, artist, source_type="youtube")

        return jsonify({
            "success": True,
            "song_id": song_id,
            "title": title,
            "artist": artist
        })
    except Exception as e:
        return jsonify({"error": f"YouTube se song add nahi ho saka: {str(e)}"}), 400


# ---------- Endpoint 4: Recorded clip identify karna ----------
@app.route("/identify", methods=["POST"])
def identify_endpoint():
    """
    Frontend se recorded audio clip (mic se record ki hui) aayegi.
    Hum usay temporarily save karke identify_song() ko denge.
    """
    if "file" not in request.files:
        return jsonify({"error": "Koi audio clip nahi mili"}), 400

    recorded_file = request.files["file"]
    # Browser se recording aksar .webm format mein aati hai - hum
    # asal extension use karte hain taake librosa/ffmpeg isay
    # sahi tarah pehchan sakein
    temp_filename = f"query_{uuid.uuid4().hex}_{recorded_file.filename}"
    temp_path = os.path.join(UPLOAD_FOLDER, temp_filename)
    recorded_file.save(temp_path)

    try:
        result = identify_song(temp_path)
    except Exception as e:
        # Ye try/except zaroori hai - iske bina agar fingerprinting
        # fail hoti (jaise ffmpeg missing hone se), Flask ka debug
        # server ek raw error page bhej deta jisme CORS headers
        # nahi hote, aur browser confusing "CORS blocked" error
        # dikhata - jabke asal masla kuch aur hota hai.
        return jsonify({"error": f"Audio process nahi ho saka: {str(e)}"}), 500
    finally:
        # Temporary query file ko delete kar dena - chahe success ho
        # ya error, ye file database mein store nahi honi chahiye
        if os.path.exists(temp_path):
            os.remove(temp_path)

    if result is None:
        return jsonify({"match": False, "message": "Song recognize nahi hua"})

    return jsonify({"match": True, **result})


if __name__ == "__main__":
    # debug=True se code change hone par server khud restart ho jata hai
    # host="0.0.0.0" se ye local network ke doosre devices se bhi accessible hoga
    app.run(debug=True, port=5000)