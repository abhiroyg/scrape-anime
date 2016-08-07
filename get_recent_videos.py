"""
This file is to be used by a `gogoanime` frequenter
and who can efficiently give the interested anime names.
TODO:
    1. Since we put all the episode titles and urls in a single
file. We should rotate them after they reach a certain size.
or just delete them after a manual confirmation that we got
what we wanted.
    2. Or put database instead of files, when the files become large.
    3. We should put the top of website's at last of our list. Doesn't matter for database, I guess.
"""
import argparse
import datetime
import json
import re
import sys

from lxml import html
import requests

from log_manager import LogManager


logger = LogManager.getLogger('latest')

def get_latest_anime(interested_filename, prev_filename,
                     ignored_filename):
    # Go to home page
    r = requests.get('http://www.gogoanime.com')
    if r.status_code != 200:
        raise Exception(
            "Could not load gogoanime.com website. Please try after some time."
        )
    logger.debug("Got the home page: {}".format(r.url))

    # Scrape the latest release list
    h = html.fromstring(r.text)
    recent_li = h.xpath("//*[@class='redgr']//li")[::-1]
    logger.debug("Extracted 'Latest episode releases'")

    try:
        with open(interested_filename) as f:
            interested = json.load(f)

        assert isinstance(interested, list)

        if not interested:
            interested = [' ']
            logger.info("Marking all anime.")
    except (FileNotFoundError, ValueError) as e:
        interested = [' ']
        logger.warn(str(e))
        logger.info("Marking all anime.")
        

    #Each term in prev [<episode_title>, <episode_url>,
    #                   <how_old>, <UTC timestamp>, <is_downloaded>]
    with open(prev_filename) as f:
        prev = json.load(f)

    assert isinstance(prev, list)

    #Each term in ignored [<episode_title>, <episode_url>,
    #                      <how_old>, <UTC timestamp>]
    with open(ignored_filename) as f:
        ignored = json.load(f)

    assert isinstance(ignored, list)

    if prev and ignored:
        last_itr = max(prev[-1][2], ignored[-1][2])
    elif prev:
        last_itr = prev[-1][2]
    elif ignored:
        last_itr = ignored[-1][2]
    else:
        last_itr = 0

    cur_itr = last_itr + 1
    prev_episode_titles = [episode[0] for episode in prev]
    ignored_episode_titles = [episode[0] for episode in ignored]

    lastseen = False
    hasnewepisodes = False

    for li in recent_li:
        # `episode_title` also contains the sub/dub/raw info
        episode_title = li.text_content().strip()

        if (episode_title in prev_episode_titles or
                episode_title in ignored_episode_titles):
            logger.info("Already marked for download/ignore: {}".format(
                         episode_title))
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
            hasnewepisodes = True
        else:
            ignored.append([episode_title, episode_url, cur_itr,
                datetime.datetime.utcnow().isoformat()]) 

    with open(prev_filename, 'w') as f:
        json.dump(prev, f, indent=2)

    with open(ignored_filename, 'w') as f:
        json.dump(ignored, f, indent=2)

    if not lastseen:
        logger.warn("We most likely missed notifications of recent anime. " + \
            "Kindly, try to run this file as frequently as possible.")

    if not hasnewepisodes:
        logger.warn("No new episodes since last run.")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
            description='Get latest anime released.',
            formatter_class=argparse.RawTextHelpFormatter)

    parser.add_argument(
            'interested_anime',
            default='resources/interested_anime.json',
            nargs='?',
            help="""Pass the path of json file that contains
list of interested anime names in lowercase.

Try to give distinctive anime names and separate words with spaces.
Example: ["one piece", "re zero", "himouto"]""")

    parser.add_argument(
            '-o', '--output-file',
            default='resources/prev.json',
            help="""The file where the latest anime are stored.""")

    parser.add_argument(
            '-g', '--ignore-file',
            default='resources/ignored.json',
            help="""The file where the ignored anime links are stored.""")

    args = parser.parse_args()
    get_latest_anime(args.interested_anime, args.output_file, args.ignore_file)
