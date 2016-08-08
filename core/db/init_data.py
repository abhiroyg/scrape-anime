import json
import os
import sqlite3


resources = os.path.join(
    os.path.abspath(os.path.join(__file__, os.pardir, os.pardir)),
    'resources'
)

conn = sqlite3.connect(os.path.join(resources, 'anime.db'))

cur = conn.cursor()

with open(os.path.join(resources, 'prev.json'), 'r') as f:
    prev = json.load(f)

cur.executemany(
    '''INSERT INTO episodes 
    (episode_title, episode_url, how_old, marked_time, 
     is_downloaded, downloaded_time) 
    VALUES (?, ?, ?, ?, ?, ?, ?)''',
    prev)

cur.execute(
    """INSERT INTO anime 
    (id, anime, anime_start_date, anime_end_date) 
    VALUES (0, 'DEFAULT', 'N/A', 'N/A')""")

conn.commit()

conn.close()
