"""
add_song.py
-----------
Ye file ek audio file leti hai, uska fingerprint banati hai
(fingerprint.py use karke), aur phir usay shazam.db mein save
kar deti hai - dono tables mein (songs aur hashes).

Ye bhi check karti hai ke 1000 songs ki limit paar to nahi ho gayi.
"""

import sqlite3
from fingerprint import fingerprint_audio

DB_NAME = "shazam.db"
MAX_SONGS = 1000   # Aapki capacity limit


def get_song_count():
    """
    Abhi tak database mein kitne songs hain, ye batata hai.
    Frontend ka counter ("50 / 1000 Songs") isi function se aayega.
    """
    connection = sqlite3.connect(DB_NAME)
    cursor = connection.cursor()
    cursor.execute("SELECT COUNT(*) FROM songs")
    count = cursor.fetchone()[0]   # fetchone() ek row deta hai, [0] uska pehla column
    connection.close()
    return count


def add_song(file_path, title, artist="Unknown", source_type="upload", source_url=None):
    """
    Naya song database mein add karti hai:
    1. Pehle check - kya limit (1000) poori ho chuki hai?
    2. Pehle check - kya ye gaana PEHLE SE database mein hai?
    3. songs table mein ek row banao (title, artist, file_path, source_url)
    4. Us song ka fingerprint (hashes) banao
    5. Sab hashes ko hashes table mein daalo, us song_id ke sath
    """

    # ---------- Step 1: Limit check ----------
    current_count = get_song_count()
    if current_count >= MAX_SONGS:
        raise Exception(f"Database full hai! Limit {MAX_SONGS} songs hai.")

    connection = sqlite3.connect(DB_NAME)
    cursor = connection.cursor()

    # ---------- Step 2: Duplicate check ----------
    # Agar YouTube se aaya hai, to same URL check karna
    # (URL sabse reliable unique pehchaan hai)
    if source_url:
        cursor.execute("SELECT id FROM songs WHERE source_url = ?", (source_url,))
        if cursor.fetchone():
            connection.close()
            raise Exception("Ye gaana pehle se database mein maujood hai (same YouTube link).")

    # Warna title+artist se check karna (case-insensitive, extra spaces ignore kar ke)
    cursor.execute(
        "SELECT id FROM songs WHERE LOWER(TRIM(title)) = LOWER(TRIM(?)) AND LOWER(TRIM(artist)) = LOWER(TRIM(?))",
        (title, artist)
    )
    if cursor.fetchone():
        connection.close()
        raise Exception(f"'{title}' pehle se database mein maujood hai.")

    # ---------- Step 3: songs table mein entry banana ----------
    cursor.execute(
        "INSERT INTO songs (title, artist, source_type, file_path, source_url) VALUES (?, ?, ?, ?, ?)",
        (title, artist, source_type, file_path, source_url)
    )

    # cursor.lastrowid us row ka ID deta hai jo abhi-abhi insert hua
    # (ye humein hashes table mein "song_id" ke liye chahiye)
    song_id = cursor.lastrowid

    # Yahan tak ka kaam save karna - taake song_id confirm ho jaye
    connection.commit()

    # ---------- Step 3: Fingerprint banana ----------
    print(f"'{title}' ka fingerprint ban raha hai, thora time lagega...")
    hashes = fingerprint_audio(file_path)   # ye fingerprint.py wala function hai

    # ---------- Step 4: Saare hashes ko database mein daalna ----------
    # executemany() ek saath bohot saari rows insert karta hai -
    # ek-ek karke insert karne se ye MUCH faster hai (26,000 hashes
    # ke liye ye farq bohot zyada matter karta hai)
    hash_rows = [(hash_value, song_id, time_offset) for hash_value, time_offset in hashes]

    cursor.executemany(
        "INSERT INTO hashes (hash_value, song_id, time_offset) VALUES (?, ?, ?)",
        hash_rows
    )

    connection.commit()
    connection.close()

    print(f"'{title}' has been added successfully. Song ID: {song_id}, Hashes stored: {len(hashes)}")
    return song_id


def update_song_source_url(song_id, source_url):
    """
    Jab kisi upload-wale song ke liye YouTube video search karke
    milta hai, usay yahan store kar dete hain - taake agli baar
    wahi gaana pehchanne par dobara search na karni pade.
    """
    connection = sqlite3.connect(DB_NAME)
    cursor = connection.cursor()
    cursor.execute("UPDATE songs SET source_url = ? WHERE id = ?", (source_url, song_id))
    connection.commit()
    connection.close()


if __name__ == "__main__":
    import sys
    if len(sys.argv) >= 3:
        file_path = sys.argv[1]
        title = sys.argv[2]
        artist = sys.argv[3] if len(sys.argv) > 3 else "Unknown"
        add_song(file_path, title, artist)
    else:
        print('Usage: python add_song.py <audio_file_path> "<title>" "<artist>"')