import json
import logging
import sys

import requests
import urllib

from lxml import html

from downloader import open_and_parse_episode_page


logging.basicConfig(stream=sys.stdout, level=logging.INFO)

downloaded_videos_file = 'downloaded_videos.txt'
with open(downloaded_videos_file, 'r', encoding='utf-8') as f:
    prev = f.readlines()
logging.info("Loaded the already downloaded episode names")

r = requests.get('http://www.gogoanime.com')
if r.status_code != 200:
    raise Exception(
        "Could not load gogoanime.com website. Please try after some time.")
logging.info("Got the home page: {}".format(r.url))

h = html.fromstring(r.text)
recent_li = h.xpath("//*[@class='redgr']//li")
logging.info("Extracted 'Latest episode releases'")

recent = []
for li in recent_li:
    episode_title = li.text_content().strip()
    if episode_title in prev:
        logging.debug("Already downloaded/ignored: {}".format(episode_title))
        continue

    recent.append(episode_title)

    subdubraw = li.xpath("./font")[0].text_content().strip('()')
    if subdubraw.lower() != 'sub':
        logging.warn("Ignoring {} as not subbed.".format(episode_title))
        continue

    episode_url = li.xpath("./a/@href")[0]
    # TODO:
    # 1. Download only those anime that interests us.
    # 2. Decouple open_and_parse_episode_page from this file.
    # This file should only get the previous list, current list and
    # compare both of them to get undownloaded list.
    # Then get the episode urls for the undownloaded list and store
    # them in a file.
    # 3. Since we put all the episode titles and urls in a single
    # file. We should rotate them after they reach a certain size.
    # or just delete them after a manual confirmation that we got
    # what we wanted.
    open_and_parse_episode_page(episode_url)
    with open(episodes_to_download, 'a') as f:
        f.write(episode_url + "\n")

if len(recent) == len(recent_li):
    logging.critical("Missed some episodes. Try running frequently from next time. :)")

with open(downloaded_videos_file, 'w') as f:
    f.write(json.dumps(recent + prev))
