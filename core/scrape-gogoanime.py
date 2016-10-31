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
from selenium import webdriver

from downloader import downloader
from log_manager import LogManager
from db.data_ops import DAO


logger = LogManager.getLogger('scraper')
# dao = DAO()

# Assuming `prev.json` is not in use by another process.
resources = os.path.join(
    os.path.abspath(os.path.join(__file__, os.path.pardir)),
    'resources'
)

prev_file = os.path.join(resources, 'prev.json')
with open(prev_file, 'r', encoding='utf-8') as f:
    prev = json.load(f)
# prev = dao.get_to_be_downloaded()
logger.info("Loaded the want-to-download anime list")

driver = webdriver.Chrome('/home/abhilash/locallib/chromedriver')
driver.maximize_window()

for i in range(len(prev)):
    # Skip, if already downloaded
    if prev[i][4]:
        continue

    start_time = datetime.datetime.utcnow().isoformat()
    success = downloader(prev[i][1], driver)
    end_time = datetime.datetime.utcnow().isoformat()

    if success:
        # dao.update_downloaded(end_time, prev[i][0])

        prev[i][4] = True
        prev[i].append(end_time)

        with open(prev_file, 'w') as f:
            json.dump(prev, f)

# Don't forget this line of code.
driver.quit()

if len(prev) == 0:
    logger.info("No anime to download.")
else:
    logger.info("Updated the anime list")

# dao.close()
