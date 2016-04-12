import json
import logging
import sys

import requests
import urllib

from lxml import html
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import WebDriverWait


logging.basicConfig(stream=sys.stdout, level=logging.INFO)

recent_videos_file = 'recent_videos.txt'
prev = []
try:
    with open(recent_videos_file, 'r') as f:
        s = f.read()
        print s
        if s != '':
            prev = json.loads(s)
except IOError as e:
    if e.strerror == 'No such file or directory':
        with open(recent_videos_file, 'w') as f:
            f.write("[]")
    else:
        raise e

r = requests.get('http://www.gogoanime.com')
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
        logging.warn("Ignoring {}".format(episode_title))
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
    logging.critical("Missed some episodes.")

with open(recent_videos_file, 'w') as f:
    f.write(json.dumps(recent + prev))


def open_and_parse_episode_page(gogoanime_episode_url):
    driver = webdriver.Chrome('/home/abhilash/locallib/chromedriver')
    driver.maximize_window()
    chunk_size = 1024

    r = requests.get(gogoanime_episode_url)
    logging.debug("Opened episode page: {}".format(r.url))

    h = html.fromstring(r.text)
    embed_video_links = h.xpath("//*[@class='postcontent']//iframe/@src")
    for embed_link in embed_video_links:
        filename = embed_link.split("/")[-1]
        logging.info("Extracted filename: {}".format(filename))

        driver.get(embed_link)
        logging.info("Opened embedded page: {}".format(r.url))
        WebDriverWait(driver, 60).until(
            expected_conditions.presence_of_element_located((
                By.XPATH, "//*[@name='flashvars']")))

        flashvars = driver.find_element_by_xpath(
            "//*[@name='flashvars']").get_attribute("value")
        flashvarsjson = json.loads(flashvars.split("config=", 1)[1])

        # bitrates = get(flashvarsjson, "bitrates")
        bitrates = flashvarsjson["playlist"][1]["bitrates"]
        logging.info("Extracted bitrates: {}".format(bitrates))

        if not isinstance(bitrates, list):
            continue

        for bitrate in bitrates:
            if bitrate['isDefault']:
                redirect_url = urllib.unquote(bitrate['url'])

        r = requests.get(redirect_url)
        if r.status_code == 302:
            logging.info("Redirecting from {}...".format(r.url))
            r = requests.get(r.headers['location'])
        logging.info("Reached the final video page: {}".format(r.url))

        logging.info("Downloading {}".format(filename))
        with open(filename, 'wb') as fd:
            for chunk in r.iter_content(chunk_size):
                fd.write(chunk)

        if not "movie" in episode_url:
            break
    driver.quit()
