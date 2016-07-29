"""
This file is to be used by a `gogoanime` frequenter
and who can efficiently give the interested anime names.
TODO:
    1. Introduce click.
    2. Since we put all the episode titles and urls in a single
file. We should rotate them after they reach a certain size.
or just delete them after a manual confirmation that we got
what we wanted.
    3. Or put database instead of files, when the files become large.
"""
import datetime
import json
import re
import sys

from lxml import html
import requests

from log_manager import LogManager


logger = LogManager.getLogger('latest')

r = requests.get('http://www.gogoanime.com')
if r.status_code != 200:
    raise Exception(
        "Could not load gogoanime.com website. Please try after some time."
    )
logger.info("Got the home page: {}".format(r.url))

h = html.fromstring(r.text)
recent_li = h.xpath("//*[@class='redgr']//li")
logger.info("Extracted 'Latest episode releases'")

# The file is a json list
# of lowercase, space separated
# strings of anime names
# ["one piece", "re zero", "himouto"]
if len(sys.argv) >= 2:
    interested_filename = sys.argv[1]
    with open(interested_filename) as f:
        interested = json.load(f)
else:
    # trimmed for `any`
    # This means, we are interested in every anime.
    interested = [' ']

if len(sys.argv) >= 3:
    prev_filename = sys.argv[2]
else:
    prev_filename = 'prev.json'

if len(sys.argv) >= 4:
    ignored_filename = sys.argv[3]
else:
    ignored_filename = 'ignored.json'

#Each term in prev [<episode_title>, <episode_url>,
#                   <how_old>, <timestamp>, <is_downloaded>]
with open(prev_filename) as f:
    try:
        prev = json.load(f)
    except ValueError:
        prev = []

#Each term in ignored [<episode_title>, <episode_url>,
#                   <how_old>, <UTC timestamp>]
with open(ignored_filename) as f:
    try:
        ignored = json.load(f)
    except ValueError:
        ignored = []

if prev and ignored:
    last_itr = max(prev[-1][2], ignored[-1][2])
elif prev:
    last_itr = prev[-1][2]
elif ignored:
    last_itr = ignored[-1][2]
else:
    last_itr = 0

cur_itr = last_itr + 1
prev_episode_titles = [entry[0] for entry in prev]
ignored_episode_titles = [entry[0] for entry in ignored]

lastseen = False
lastrunseen = False

for li in recent_li:
    # `episode_title` also contains the sub/dub/raw info
    episode_title = li.text_content().strip()
    if (episode_title in prev_episode_titles or
            episode_title in ignored_episode_titles):
        logger.debug("Already downloaded/ignored: {}".format(episode_title))
        lastseen = True
        continue

    episode_url = li.xpath("./a/@href")[0]

    subdubraw = li.xpath("./font")[0].text_content().strip('()')
    if subdubraw.lower() != 'sub':
        logger.warn("Ignoring {}, as it's not subbed.".format(episode_title))
        ignored.append([episode_title, episode_url, cur_itr,
            datetime.datetime.utcnow().isoformat()]) 
        continue

    temp = re.sub(r'[^a-zA-Z0-9]+', ' ', episode_title).lower()
    if any(x in temp for x in interested):
        prev.append([episode_title, episode_url, cur_itr,
            datetime.datetime.utcnow().isoformat(), False])
        logger.info("Storing {}".format(episode_title))
        lastrunseen = True
    else:
        ignored.append([episode_title, episode_url, cur_itr,
            datetime.datetime.utcnow().isoformat()]) 

with open(prev_filename, 'w') as f:
    json.dump(prev, f)

with open(ignored_filename, 'w') as f:
    json.dump(ignored, f)

if not lastseen:
    logger.warn("We most likely missed notifications of recent anime." + \
        "Kindly, try to run this file as frequently as possible.")

if not lastrunseen:
    logger.warn("No new episodes came out.")
