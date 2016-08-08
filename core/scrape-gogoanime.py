"""
Don't let the `prev.json` file to be used by
both this and `get_recent_vidoes.py` at the
same time
"""
import datetime
import json
import os
import sys

import requests
from lxml import html

from downloader import downloader
from log_manager import LogManager


logger = LogManager.getLogger('scraper')

# Assuming `prev.json` is not in use by another process.
resources = os.path.join(
    os.path.abspath(os.path.join(__file__, os.path.pardir)),
    'resources'
)
prev_file = os.path.join(resources, 'prev.json')
with open(prev_file, 'r', encoding='utf-8') as f:
    prev = json.load(f)
logger.info("Loaded the want-to-download anime list")

for i in range(len(prev)):
    # If it is already downloaded
    if prev[i][4]:
        continue
    start_time = datetime.datetime.utcnow().isoformat()
    downloader(prev[i][1])
    end_time = datetime.datetime.utcnow().isoformat()
    prev[i][4] = True
    prev[i].append(end_time)
    with open(prev_file, 'w') as f:
        json.dump(prev, f)

logger.info("Updated the anime list")
