"""
delete_song.py
--------------
Kisi bhi song ko uski ID se database se hatane ke liye
(uske hashes samet).

Chalane ka tareeqa: python delete_song.py <song_id>
Pehle "python list_songs.py" chala kar ID confirm kar lein.
"""

import sqlite3
import sys

DB_NAME = "shazam.db"


def delete_song(song_id):
    connection = sqlite3.connect(DB_NAME)
    cursor = connection.cursor()

    cursor.execute("SELECT title, artist FROM songs WHERE id = ?", (song_id,))
    song = cursor.fetchone()

    if not song:
        print(f"Song ID {song_id} nahi mila.")
        connection.close()
        return

    cursor.execute("DELETE FROM hashes WHERE song_id = ?", (song_id,))
    cursor.execute("DELETE FROM songs WHERE id = ?", (song_id,))
    connection.commit()
    connection.close()

    print(f"Delete ho gaya: [{song_id}] {song[0]} - {song[1]}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python delete_song.py <song_id>")
    else:
        delete_song(int(sys.argv[1]))