import json
import sqlite3

conn = sqlite3.connect('anime.db')

c = conn.cursor()

with open('../resources/prev.json', 'r') as f:
    prev = json.load(f)

prev = [p[:5] for p in prev]

c.executemany('INSERT INTO episodes (episode_title, episode_url, how_old, marked_time, is_downloaded) VALUES (?, ?, ?, ?, ?)', prev)

c.execute("INSERT INTO anime (id, anime, anime_start_date, anime_end_date) VALUES (0, 'DEFAULT', 'N/A', 'N/A')")

conn.commit()

conn.close()
