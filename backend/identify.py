"""
identify.py
-----------
Ye file wahi kaam karti hai jo asal Shazam karta hai:
Ek recorded audio clip leti hai, uska fingerprint banati hai,
aur database mein dhoondti hai ke ye kaunse song se sabse zyada
"time-consistent" match karta hai.
"""

import sqlite3
from collections import defaultdict
from fingerprint import fingerprint_audio

DB_NAME = "shazam.db"

# Kam se kam itne "consistent" matching hashes chahiye taake
# hum confidently keh sakein "ye wahi song hai" (warna "no match")
MIN_MATCH_THRESHOLD = 5


def find_matches_in_db(query_hashes):
    """
    Query clip ke saare hashes ko database mein dhoondti hai.
    Har match ke sath ye bhi return karti hai: kaunsa song_id,
    aur database mein wo hash kis time_offset par tha.
    """
    connection = sqlite3.connect(DB_NAME)
    cursor = connection.cursor()

    # Query se aaye hashes ko ek dictionary mein daalte hain:
    # hash_value -> query_time_offset
    # (taake baad mein hume pata ho ye hash HAMARE clip mein kis waqt tha)
    query_hash_map = {h: t for h, t in query_hashes}

    hash_list = list(query_hash_map.keys())

    # Database mein ek saath saare hashes ke against dekhna hai.
    # SQLite ek query mein zyada se zyada ~900 placeholders leta hai,
    # isliye hum hashes ko chote-chote batches (chunks) mein todte hain.
    chunk_size = 500
    all_db_matches = []

    for i in range(0, len(hash_list), chunk_size):
        chunk = hash_list[i:i + chunk_size]
        placeholders = ",".join("?" for _ in chunk)
        query = f"""
            SELECT hash_value, song_id, time_offset
            FROM hashes
            WHERE hash_value IN ({placeholders})
        """
        cursor.execute(query, chunk)
        all_db_matches.extend(cursor.fetchall())

    connection.close()
    return all_db_matches, query_hash_map


def score_candidates(all_db_matches, query_hash_map):
    """
    Ye function decide karti hai ke kaunsa song sabse zyada
    "sahi" match hai.

    Idea ye hai: agar humara clip sach mein kisi song ka hissa hai,
    to matching hashes ka TIME-DIFFERENCE (db_time - query_time)
    HAMESHA SAME rahega. Ye "alignment" hi asli proof hai match ka -
    sirf hash match hona kaafi nahi (wo coincidence bhi ho sakta hai).
    """

    # Har song ke liye: delta (time-difference) ki counting
    # Structure: { song_id: { delta_value: count } }
    song_delta_counts = defaultdict(lambda: defaultdict(int))

    for hash_value, song_id, db_time_offset in all_db_matches:
        query_time_offset = query_hash_map[hash_value]

        # Ye woh "alignment check" hai - agar clip sahi song ka
        # hissa hai, to ye delta baar baar SAME milega
        delta = db_time_offset - query_time_offset

        song_delta_counts[song_id][delta] += 1

    # Ab har candidate song ke liye best score nikaalna
    # (uska sabse zyada baar aaya hua delta count)
    best_song_id = None
    best_score = 0

    for song_id, delta_counts in song_delta_counts.items():
        # is song ka sabse consistent delta kaunsa hai, aur kitni
        # baar wo repeat hua
        top_score = max(delta_counts.values())

        if top_score > best_score:
            best_score = top_score
            best_song_id = song_id

    return best_song_id, best_score


def get_song_info(song_id):
    """Database se song ka title/artist nikaalti hai."""
    connection = sqlite3.connect(DB_NAME)
    cursor = connection.cursor()
    cursor.execute("SELECT title, artist FROM songs WHERE id = ?", (song_id,))
    result = cursor.fetchone()
    connection.close()
    return result


def identify_song(audio_path):
    """
    Main function - isay backend API call karegi.
    Recorded clip ka path leti hai, aur match (ya None) return karti hai.
    """
    print("Recorded clip ka fingerprint ban raha hai...")
    query_hashes = fingerprint_audio(audio_path)

    print("Database mein match dhoonda ja raha hai...")
    all_db_matches, query_hash_map = find_matches_in_db(query_hashes)

    best_song_id, best_score = score_candidates(all_db_matches, query_hash_map)

    # Agar best score bhi threshold se kam hai, to confidently
    # match nahi bol sakte - "no match found" bolna zyada sahi hai
    if best_song_id is None or best_score < MIN_MATCH_THRESHOLD:
        print("Koi match nahi mila.")
        return None

    title, artist = get_song_info(best_song_id)
    print(f"Match mil gaya: '{title}' by {artist} (confidence score: {best_score})")

    return {"title": title, "artist": artist, "confidence": best_score}


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        identify_song(sys.argv[1])
    else:
        print("Usage: python identify.py <recorded_clip_path>")