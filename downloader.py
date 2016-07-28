"""
This function is to be used by a `gogoanime` frequenter
and who can deduce that the anime/movie to be downloaded
has multiple parts.
"""
import argparse
import json
import logging
import sys

import requests

from clint.textui import progress
from lxml import html
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import WebDriverWait
from urllib.parse import unquote


def open_and_parse_episode_page(
        gogoanime_episode_url, has_multiple_parts=False,
        download_which='all', output_folder='.',
        verbose=0, series=False):

    # TODO: Give leeway to download selected parts
    # if the video has multiple parts. (`download_which`)
    # Examples:
    #   1-3,5-9,13-15
    #       - Download 1st, 2nd, 3rd, 5th, 6th, 7th, 8th, 9th, 13th,
    #         14th, and 15th parts of the video.
    #   1,3-10,15
    #       - Similarly, download 1st, 3rd-10th and 15th parts.
    #   1:1-3,5:4-10,3-7
    #       - Applicable only when `series` is true.
    #       - Download 1-3 parts of 1st episode, 4-10 parts of 5th episode and
    #         3-7 parts of remaining episodes.

    if verbose >= 1:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    # Initialize the driver
    driver = webdriver.Chrome('/home/abhilash/locallib/chromedriver')
    driver.maximize_window()
    chunk_size = 1024

    while True:
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
                for chunk in progress.bar(r.iter_content(chunk_size),
                        expected_size=(total_length/chunk_size + 1)):
                    if chunk:
                        fd.write(chunk)
                        fd.flush()

            if not has_multiple_parts:
                break
        if not series:
            break
        else:
            # We might miss some special episodes if we do it this way.
            # Always check for special episodes and download them individually.
            logging.warn("We might miss some special episodes. " + \
                "Check for them and download them individually.")
            remurl, epnum = gogoanime_episode_url.rsplit('-', 1)
            gogoanime_episode_url = '-'.join([remurl, str(int(epnum) + 1)])
    driver.quit()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
            description='Download anime episode/movie from gogoanime.',
            formatter_class=argparse.RawTextHelpFormatter)

    parser.add_argument('url',
            help='The gogoanime URL which contains the video(s).')

    parser.add_argument('-m', '--has_multiple_parts',
            action='store_true',
            help="""Is the video split in multiple parts ?
(All parts being available in the same URL.)

You only have to give "-m" (without quotes), if
the video has multiple parts. Don't give it, if
the video does not.""")

    parser.add_argument('-w', '--download_which',
            default='all',
            help="""Which parts of the video you want to download.
Examples:
    1,3-10,15
    11-20,1-9
    1-100,5-7
    100-87,77-54
1 being the first part and so on.
By default, we download all parts.""")

    parser.add_argument('-o', '--output_folder',
            default='.',
            help="""Where do you want to download the video ?
By default, we download to the current folder.""")

    parser.add_argument('-s', '--series',
            action='store_true',
            help="""Do you want us to download all the videos
that came after this too ?

You only have to give "-s" (without quotes), if
you want us to. Don't give it otherwise.""")

    parser.add_argument('-v', '--verbose',
            action='count',
            default=0)

    args = parser.parse_args()
    open_and_parse_episode_page(
        args.url, args.has_multiple_parts,
        args.download_which, args.output_folder,
        args.verbose, args.series
    )
