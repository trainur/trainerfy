import sqlite3 as sql
import os
from flask import current_app as app
import databuilder

AUDIO_TABLE_NAME = databuilder.AUDIO_TABLE_NAME
FINGERPRINT_TABLE_NAME = databuilder.FINGERPRINT_TABLE_NAME
DATABASE_NAME = databuilder.DATABASE_NAME
DATABASE_PATH = databuilder.DATABASE_PATH

def find_associated_fingerprints(h):
    if not os.path.isfile(DATABASE_PATH):
        return False
    
    conn = sql.connect(DATABASE_PATH)

    try:
        c = conn.cursor()
        c.execute(f"""
                SELECT
                  song_id,
                  time_offset
                FROM {FINGERPRINT_TABLE_NAME}
                WHERE hash = ?
        """, (h,))

        matches = c.fetchall()

    finally:
        conn.close()

    return matches

def fetch_song(song_id):
    app.logger.info(f"[fetch_song] called with song_id={song_id}")

    if not os.path.isfile(DATABASE_PATH):
        return False
    
    conn = sql.connect(DATABASE_PATH)

    try:
        c = conn.cursor()
        c.execute(f"""
                SELECT
                  id,
                  title,
                  artist,
                  album,
                  artwork,
                  artwork_mime
                FROM {AUDIO_TABLE_NAME}
                WHERE id = ?
                  """, (song_id,))

        match = c.fetchone()

    finally:
        conn.close()

    app.logger.info(f"[fetch_song] returning id={match[0] if match else None}")

    return match

def song_fingerprint_counts():
    if not os.path.isfile(DATABASE_PATH):
        return False
    
    conn = sql.connect(DATABASE_PATH)

    try:
        c = conn.cursor()
        c.execute(f"""
                SELECT
                  song_id,
                  COUNT(*)
                FROM {FINGERPRINT_TABLE_NAME}
                GROUP BY song_id
                  """)

        counts = c.fetchall()

    finally:
        conn.close()

    return dict(counts)