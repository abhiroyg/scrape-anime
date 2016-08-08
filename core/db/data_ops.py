import os
import sqlite3


class DAO:
    def __init__(self):
        resources = os.path.join(
            os.path.abspath(os.path.join(__file__, os.pardir, os.pardir)),
            'resources'
        )
        self.conn = sqlite3.connect(os.path.join(resources, 'anime.db'))

        self.cur = self.conn.cursor()

    def in_database(self, episode_title):
        self.cur.execute(
            'SELECT * FROM episodes WHERE episode_title=?',
            episode_title
        )
        return self.cur.fetchone() is not None

    def insert_ignore(self, entry):
        # if it is a new anime
        # fetch its data from anime-planet (?)
        # and update `anime` table.
        self.cur.execute(
            '''INSERT INTO episodes 
            (episode_title, episode_url, how_old, 
            marked_time, is_ignored) 
            VALUES (?, ?, ?, ?, 1)''',
            entry
        )
        self.conn.commit()

    def insert_download(self, episode_title, episode_url,
            cur_itr, marked_date):
        # if it is a new anime
        # fetch its data from anime-planet (?)
        # and update `anime` table.
        self.cur.execute(
            '''INSERT INTO episodes 
            (episode_title, episode_url, how_old, marked_time) 
            VALUES (?, ?, ?, ?)''',
            entry
        )
        self.conn.commit()

    def get_to_be_downloaded(self):
        self.cur.execute(
            '''SELECT episode_title, episode_url
            FROM episodes WHERE is_downloaded=0 
            AND is_ignored=0'''
        )
        return self.cur.fetchall()

    def update_downloaded(self, downloaded_time, episode_title):
        self.cur.execute(
            '''UPDATE episodes 
            SET is_downloaded=1, downloaded_time=?
            WHERE episode_title=?''',
            downloaded_time, episode_title
        )
        self.conn.commit()

    def close(self):
        self.conn.close()
