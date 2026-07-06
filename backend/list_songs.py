"""
list_songs.py
-------------
Ye ek simple debugging tool hai - database mein abhi kaunse
songs maujood hain, ye dikhata hai. Isse pata chalta hai ke
koi gaana "missing" to nahi hai.

Chalane ka tareeqa: python list_songs.py
"""

import sqlite3

DB_NAME = "shazam.db"

connection = sqlite3.connect(DB_NAME)
cursor = connection.cursor()
cursor.execute("SELECT id, title, artist, source_type, source_url FROM songs ORDER BY id")
songs = cursor.fetchall()
connection.close()

if not songs:
    print("Database mein koi song nahi hai!")
else:
    print(f"Total {len(songs)} songs database mein maujood hain:\n")
    for song_id, title, artist, source_type, source_url in songs:
        print(f"  [{song_id}] {title} - {artist}  (source: {source_type})")