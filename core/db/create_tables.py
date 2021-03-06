import os
import sqlite3


resources = os.path.join(
    os.path.abspath(os.path.join(__file__, os.pardir, os.pardir)),
    'resources'
)
conn = sqlite3.connect(os.path.join(resources, 'anime.db'))

cur = conn.cursor()

cur.execute('''CREATE TABLE episodes
             (id integer PRIMARY KEY AUTOINCREMENT,
              episode_title text UNIQUE NOT NULL,
              episode_url text UNIQUE NOT NULL,
              how_old integer NOT NULL,
              marked_time text NOT NULL,
              downloaded_time text NOT NULL DEFAULT "NA",
              size real NOT NULL DEFAULT 0.0,
              is_downloaded integer NOT NULL DEFAULT 0,
              is_ignored integer NOT NULL DEFAULT 0,
              anime_id integer NOT NULL DEFAULT 0 REFERENCES anime (id) ON DELETE NO ACTION)''')

cur.execute('''CREATE TABLE anime
             (id integer PRIMARY KEY AUTOINCREMENT,
              anime text UNIQUE NOT NULL,
              alternative_names text,
              anime_start_date text NOT NULL,
              anime_end_date text NOT NULL,
              status text DEFAULT "watching" NOT NULL,
              anime_type text DEFAULT "tv" NOT NULL,
              parent_id integer DEFAULT id NOT NULL)''')

conn.commit()
conn.close()
