import sqlite3

conn = sqlite3.connect('../resources/anime.db')

c = conn.cursor()

c.execute('''CREATE TABLE episodes
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

c.execute('''CREATE TABLE anime
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
