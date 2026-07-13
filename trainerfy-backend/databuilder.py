import os
import sqlite3 as sql
from mutagen.id3 import ID3, ID3NoHeaderError
import base64
import argparse
import fingerprinter
import shutil

AUDIO_TABLE_NAME = "audio_data"
FINGERPRINT_TABLE_NAME = "fingerprint_data"
DATABASE_NAME = "audio_data"
DATABASE_PATH = f"./{DATABASE_NAME}"

MUSIC_FOLDER = "/home/trainer/Music/trainerfy"

def audio_exists(file_name):
    if not os.path.isfile(DATABASE_PATH):
        print("Database does not exist. Create one using -b or --build.")
        return False
    
    conn = sql.connect(DATABASE_PATH)

    try:
        c = conn.cursor()
        c.execute(f"SELECT title FROM {AUDIO_TABLE_NAME} WHERE title = ?", (file_name,))
        result = c.fetchone()
        return result is not None

    finally:
        conn.close()

def create_database():
    if os.path.isfile(DATABASE_PATH):
        print("Database already exists. Use -c or --clear to clear it.")
        return
    
    conn = sql.connect(DATABASE_PATH)

    try:
        c = conn.cursor()

        c.execute("PRAGMA foreign_keys = ON")

        c.execute(f"""
            CREATE TABLE IF NOT EXISTS {AUDIO_TABLE_NAME} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                artist TEXT,
                album TEXT,
                artwork TEXT,
                artwork_mime TEXT
            )
        """)

        c.execute(f"""
            CREATE TABLE IF NOT EXISTS {FINGERPRINT_TABLE_NAME} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                song_id INTEGER NOT NULL,
                hash INTEGER NOT NULL,
                time_offset INTEGER NOT NULL,
                FOREIGN KEY (song_id) REFERENCES {AUDIO_TABLE_NAME}(id) ON DELETE CASCADE
            )
        """)

        c.execute(f"""
            CREATE INDEX IF NOT EXISTS idx_fingerprints_hash
            ON {FINGERPRINT_TABLE_NAME}(hash)
        """)

        conn.commit()

    finally:
        conn.close()

def clear_database():
    if not os.path.isfile(DATABASE_PATH):
        print("Database does not exist. Create a new one with -b or --build.")
        return

    conn = sql.connect(DATABASE_PATH)

    try:
        c = conn.cursor()
        c.execute(f"DELETE FROM {AUDIO_TABLE_NAME}")
        c.execute(f"DELETE FROM {FINGERPRINT_TABLE_NAME}")

        conn.commit()
    finally:
        conn.close()

def retrieve_stored_audio_data():
    if not os.path.isfile(DATABASE_PATH):
        print("Database does not exist. Create a new one with -b or --build")
        return

    conn = sql.connect(DATABASE_PATH)

    try:
        c = conn.cursor()
        c.execute(f"SELECT id, title, artist, album FROM {AUDIO_TABLE_NAME}")

        rows = c.fetchall()
    finally:
        conn.close()

    return rows

def retrieve_fingerprint_summary():
    if not os.path.isfile(DATABASE_PATH):
        print("Database does not exist. Create a new one with -b or --build")
        return

    conn = sql.connect(DATABASE_PATH)

    try:
        c = conn.cursor()
        c.execute(f"""
            SELECT
                song_id,
                COUNT(*) AS total_fingerprints,
                COUNT(DISTINCT hash) AS unique_hashes,
                MIN(time_offset) AS min_offset,
                MAX(time_offset) AS max_offset
            FROM {FINGERPRINT_TABLE_NAME}
            GROUP BY song_id
            ORDER BY song_id
        """)

        rows = c.fetchall()
    finally:
        conn.close()

    return rows

def save_to_database(metadata, fingerprint):
    conn = sql.connect(DATABASE_PATH)

    try:
        c = conn.cursor()
        c.execute("PRAGMA foreign_keys = ON")

        # Insert the song metadata first
        c.execute(f"""
            INSERT INTO {AUDIO_TABLE_NAME} (title, artist, album, artwork, artwork_mime)
            VALUES (?, ?, ?, ?, ?)
        """, (
            metadata["title"],
            metadata["artist"],
            metadata["album"],
            metadata["artwork"],
            metadata["artwork_mime"]
        ))

        # Get the ID of the song we just inserted
        song_id = c.lastrowid

        # Insert all fingerprints linked to that song
        c.executemany(f"""
            INSERT INTO {FINGERPRINT_TABLE_NAME} (song_id, hash, time_offset)
            VALUES (?, ?, ?)
        """, [
            (song_id, int(hash_value), int(time_offset))
            for hash_value, time_offset in fingerprint
        ])

        conn.commit()

    finally:
        conn.close()

def read_metadata(audio_path):
    try:
        tags = ID3(audio_path)
    except ID3NoHeaderError:
        return {
            "title": "Unknown Title",
            "artist": "Unknown Artist",
            "album": "Unknown Album",
            "artwork": None,
            "artwork_mime": None
        }

    artwork_base64 = None
    artwork_mime = None

    pictures = tags.getall("APIC")

    if pictures:
        picture = pictures[0]
        artwork_base64 = base64.b64encode(picture.data).decode("utf-8")
        artwork_mime = picture.mime

    metadata = {
        "title": tags.get("TIT2").text[0] if tags.get("TIT2") else "Unknown Title",
        "artist": tags.get("TPE1").text[0] if tags.get("TPE1") else "Unknown Artist",
        "album": tags.get("TALB").text[0] if tags.get("TALB") else "Unknown Album",
        "artwork": artwork_base64,
        "artwork_mime": artwork_mime
    }

    return metadata

def generate_database(file_path = MUSIC_FOLDER, save_spectrogram=False):
    if not os.path.isfile(DATABASE_PATH):
        print("Database does not exist. Create one using -n or --new.")
        return
    
    if not os.path.isdir(file_path):
        print(f"Specified path {file_path} is not a directory.")
        return

    if os.path.isdir(fingerprinter.SPECTROGRAM_PATH):
        shutil.rmtree(fingerprinter.SPECTROGRAM_PATH, ignore_errors=True)

    for filename in os.listdir(file_path):
        if filename.endswith(".mp3"):
            audio_path = os.path.join(file_path, filename)
            metadata = read_metadata(audio_path)

            if audio_exists(metadata["title"]):
                print(f"Skipping {filename} - title '{metadata['title']}' already in database")
                continue

            fingerprint = fingerprinter.generate_song_fingerprint(audio_path, save_spectrogram)
            save_to_database(metadata, fingerprint)

###########################################################################################################################

parser = argparse.ArgumentParser(description="Trainerfy database builder")
parser.add_argument("-c", "--clear", action="store_true", help="Clear the database")
parser.add_argument("-n", "--new", action="store_true", help="Creates a new database file")
parser.add_argument("-b", "--build", action="store_true", help=f"Builds the database, without overwriting existing audio data. Default load directory is {MUSIC_FOLDER}. You can specify the load directory with -d (--directory)")
parser.add_argument("-d", "--directory", type=str, help="Specify directory to load audio from")
parser.add_argument("-l", "--list", action="store_true", help="Lists the audio files stored in the database")
parser.add_argument("-f", "--fingerprint", action="store_true", help="Include fingerprint summary information")
parser.add_argument("-s", "--spectrogram", action="store_true", help="Save spectrogram images for each audio file while building")

args=parser.parse_args()

if args.clear:
    print("Clearing database")
    clear_database()
    print("Done!")

if args.new:
    print("Creating a new database")
    create_database()
    print("Done!")

if args.build:
    folder = args.directory if args.directory else MUSIC_FOLDER
    save_spectrogram = args.spectrogram
    print(f"Building database from {folder}")
    print(f"Save spectrograms: {'Yes' if save_spectrogram else 'No'}")
    generate_database(folder, save_spectrogram)
    print("Done!")

if args.list:
    print(retrieve_stored_audio_data())

if args.fingerprint:
    rows = retrieve_fingerprint_summary()

    for row in rows:
        song_id, total, unique_hashes, min_offset, max_offset = row 
        print(f"Song ID: {song_id}")
        print(f"  Total fingerprints: {total}")
        print(f"  Unique hashes:       {unique_hashes}")
        print(f"  Time offset range:   {min_offset} -> {max_offset}")
        print("-" * 40)