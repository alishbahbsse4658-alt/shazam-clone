"""
database.py
------------
Ye file sirf ek kaam karti hai: SQLite database aur uske andar
zaroori tables bana deti hai. Isko sirf EK BAAR chalana hota hai
(project shuru karte waqt), phir baaki saari files isi database
file ko use karengi.
"""

import sqlite3

# Database file ka naam. Ye file khud-ba-khud ban jayegi
# jab pehli baar connect() call hoga (agar pehle se nahi hai).
DB_NAME = "shazam.db"


def create_tables():
    # sqlite3.connect() database file se connection kholta hai.
    # Agar "shazam.db" pehle se maujood nahi, to ye nayi file bana degi.
    connection = sqlite3.connect(DB_NAME)

    # cursor() ek object deta hai jiske zariye hum SQL commands
    # run kar sakte hain (jaise CREATE TABLE, INSERT, SELECT waghera).
    cursor = connection.cursor()

    # ---------- Table 1: songs ----------
    # Ye table har song ki basic details store karegi.
    #
    # id           -> har song ko unique number milega (auto badhta jayega)
    # title        -> song ka naam
    # artist       -> singer/artist ka naam
    # source_type  -> "upload" ya "youtube" (song kahan se aaya)
    # file_path    -> audio file kahan save hai (server ke disk par)
    # added_at     -> kis waqt ye song add hua (record rakhne ke liye)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS songs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            artist TEXT,
            source_type TEXT NOT NULL,
            file_path TEXT NOT NULL,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ---------- Table 2: hashes ----------
    # Ye table hamara "fingerprint" data store karegi.
    # Har song ke hazaron hashes ban sakte hain, isliye ye table
    # songs table se bahut bari hogi.
    #
    # id           -> har hash row ka apna unique number
    # hash_value   -> wo fingerprint hash jo audio se generate hoga
    #                 (ye column sabse zyada important hai kyunke
    #                  isi par search hoga)
    # song_id      -> ye hash kis song se belong karta hai
    #                 (songs table ke id se linked - FOREIGN KEY)
    # time_offset  -> song ke andar ye hash kis waqt (milliseconds
    #                 mein) mila tha
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS hashes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hash_value TEXT NOT NULL,
            song_id INTEGER NOT NULL,
            time_offset INTEGER NOT NULL,
            FOREIGN KEY (song_id) REFERENCES songs (id)
        )
    """)

    # ---------- Index banana (sabse zaroori step) ----------
    # Ye woh cheez hai jo lookup ko FAST banati hai (jaisa humne
    # pehle discuss kiya tha - O(1) jaisi speed).
    # Bina index ke, database har baar hash_value dhoondne ke liye
    # poori table scan karegi (slow / brute-force jaisa).
    # Index ke sath, ye seedha us row par pahunch jati hai.
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_hash_value
        ON hashes (hash_value)
    """)

    # Changes ko permanently save karne ke liye commit() zaroori hai.
    # Iske bina, saara kaam sirf memory mein rehta, file mein save nahi hota.
    connection.commit()

    # Connection band karna, taake koi file lock na reh jaye.
    connection.close()

    print(f"Database '{DB_NAME}' has been created, both tables (songs, hashes) are ready.")


# Ye Python ka standard tareeqa hai kehne ka:
# "sirf tab ye function chalao jab is file ko DIRECTLY run kiya jaye"
# (na ke jab koi doosri file isko import kare)
if __name__ == "__main__":
    create_tables()