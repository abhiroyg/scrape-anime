"""
This function is to be used by a `gogoanime` frequenter
and who can deduce that the anime/movie to be downloaded
has multiple parts.
"""
import json
import logging
import sys

import click
import requests

from clint.textui import progress
from lxml import html
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import WebDriverWait
from urllib.parse import unquote


@click.command()
@click.argument('gogoanime_episode_url')
@click.argument('has_multiple_parts', default=False)
@click.argument('download_which', default='all')
@click.option('-o', '--output_folder', default='.')
@click.option('-v', '--verbose', count=True)
def open_and_parse_episode_page(gogoanime_episode_url, has_multiple_parts, download_which, output_folder, verbose):
    # TODO: Give leeway to download selected parts
    # if the video has multiple parts. (`download_which`)
    # Examples:
    #   1-3, 5-9, 13-15
    #   1,3-10,15
    if verbose >= 1:
        logging.basicConfig(level=logging.DEBUG)

    # Initialize the driver
    driver = webdriver.Chrome('/home/abhilash/locallib/chromedriver')
    driver.maximize_window()
    chunk_size = 1024

    # Open the episode/ova/movie page
    r = requests.get(gogoanime_episode_url)
    assert gogoanime_episode_url == r.url
    logging.debug("Opened episode page: {}".format(r.url))

    # Prints out all the video links in the page.
    h = html.fromstring(r.text)
    embedded_video_links = h.xpath("//*[@class='postcontent']//iframe/@src")
    if len(embedded_video_links) == 0:
        logging.info("No video links exist in this page.")
        return

    # Used for naming the files as `part1`, `part2`, ...
    part = 1

    if output_folder[-1] != '/':
        output_folder += '/'

    # Extract each url and download
    for embedded_link in embedded_video_links:
        # Create the filename
        filename = output_folder + gogoanime_episode_url.split("/")[-1]

        if has_multiple_parts:
            filename += '_part_' + str(part)
            part += 1

        if '.flv' in embedded_link:
            filename += '.flv'
        elif '.mkv' in embedded_link:
            filename += '.mkv'
        else:
            filename += '.mp4'

        logging.info("Extracted filename: {}".format(filename))


        # Get the downloadble link
        driver.get(embedded_link)
        logging.debug("Opened embedded page: {}".format(embedded_link))
        WebDriverWait(driver, 60).until(
            expected_conditions.presence_of_element_located((
                By.XPATH, "//*[@name='flashvars']")))

        flashvars = driver.find_element_by_xpath(
            "//*[@name='flashvars']").get_attribute("value")
        flashvarsjson = json.loads(flashvars[len("config="):])

        # We have to search all over the dictionary to
        # find this, if so it will take a lot of time
        # for the search to finish.
        # bitrates = get(flashvarsjson, "bitrates")

        bitrates = flashvarsjson["playlist"][1]["bitrates"]
        logging.debug("Extracted bitrates: {}".format(bitrates))

        if not isinstance(bitrates, list):
            bitrates = [bitrates]

        # Download the url with lowest bitrate.
        # Generally it's the default. TODO. Confirm it.
        for bitrate in bitrates:
            if bitrate['isDefault']:
                redirect_url = unquote(bitrate['url'])

        # Go through redirection till you reach
        # the final downloadable page.
        r = requests.get(redirect_url, stream=True)
        while r.status_code == 302:
            logging.debug("Redirecting from {}...".format(r.url))
            r = requests.get(r.headers['location'], stream=True)
        logging.debug("Reached the final video page: {}".format(r.url))

        
        # Download the video
        # Learnt from http://stackoverflow.com/questions/15644964/python-progress-bar-and-downloads
        logging.info("Downloading {}".format(filename))
        with open(filename, 'wb') as fd:
            total_length = int(r.headers['content-length'])
            for chunk in progress.mill(r.iter_content(chunk_size),
                    expected_size=(total_length/chunk_size + 1)):
                if chunk:
                    fd.write(chunk)
                    fd.flush()

        if not has_multiple_parts:
            break
    driver.quit()

if __name__ == '__main__':
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    open_and_parse_episode_page()
