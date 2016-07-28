"""
Don't let the `prev.json` file to be used by
both this and `get_recent_vidoes.py` at the
same time
"""
import json
import sys

import requests


from lxml import html

from downloader import open_and_parse_episode_page
from log_manager import LogManager


logger = LogManager.getLogger('scraper')

# Assuming `prev.json` is not in use by another process.
prev_file = 'prev.json'
with open(prev_file, 'r', encoding='utf-8') as f:
    prev = json.load(f)
logger.info("Loaded the want-to-download anime list")

for i in range(len(prev)):
    # If it is already downloaded
    if prev[i][4]:
        continue
    open_and_parse_episode_page(prev[i][1])
    prev[i][4] = True

with open(prev_file, 'w') as f:
    json.dump(prev, f)
logger.info("Updated the anime list")
