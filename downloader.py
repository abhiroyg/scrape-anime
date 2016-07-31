"""
This function is to be used by a `gogoanime` frequenter
and who can deduce that the anime/movie to be downloaded
has multiple parts.
"""
import argparse
import json
import sys

from clint.textui import progress
from lxml import html
import requests
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import WebDriverWait
from urllib.parse import unquote

from log_manager import LogManager


logger = LogManager.getLogger('downloader')

def get_embedded_video_links(gogoanime_episode_url):
    """
    TODO:
    Common url is:
        http://www.gogoanime.com/battery-episode-3
    But, some episodes will have urls like
        http://www.gogoanime.com/battery-episode-3-episode-3
    So, this function if it could not find videos
    in the common url. It will go to previous page
    if it exists and clicks <Next episode>.
    Sometimes, <Next episode> leads to a `movie/special/ova/ona`
    page, so it will skip those and gets the correct url.
    """

    # Open the episode/ova/ona/special/movie page
    r = requests.get(gogoanime_episode_url)

    assert gogoanime_episode_url == r.url
    logger.debug("Opened episode page: {}".format(r.url))

    # Prints out all the video links in the page.
    h = html.fromstring(r.text)
    embedded_video_links = h.xpath("//*[@class='postcontent']//iframe/@src")
    return embedded_video_links

def get_downloadable_links(embedded_link, driver):
    """
    Get the downloadable link.

    We had to use Selenium mainly for this task.
    Using `requests`, the webpage of `embedded_link`
    is not giving us `flashvars`.

    The returned links are not the final downloadable links
    but they redirect to it. Generally two redirects.
    """

    # Other URLs have different json structure in "playlist"
    # In some it's flashvarsjson["playlist"][1]["bitrates"][k]["url"]
    # In some, flashvarsjson["playlist"][2]["bitrates"][k]["url"]
    # In some, flashvarsjson["playlist"][1]["url"]
    # One thing I noticed is, we should ignore 
    # flashvarsjson["playlist"][k]["provider"] == "ima"
    # and take
    # flashvarsjson["playlist"][k]["provider"] == "pseudostreaming"

    driver.get(embedded_link)
    logger.debug("Opened embedded page: {}".format(embedded_link))
    (
        WebDriverWait(driver, 60)
        .until(expected_conditions
               .presence_of_element_located(
                   (By.XPATH, "//*[@name='flashvars']")
              ))
    )

    flashvars = (
        driver
        .find_element_by_xpath("//*[@name='flashvars']")
        .get_attribute("value")
    )
    flashvarsjson = json.loads(flashvars[len("config="):])

    playlist = flashvarsjson["playlist"][-1]
    assert playlist["provider"] != "ima"
    assert playlist["provider"] == "pseudostreaming"
    if "bitrates" in playlist:
        bitrates = playlist["bitrates"]
    else:
        bitrates = playlist
        bitrates["isDefault"] = True
    logger.debug("Extracted bitrates: {}".format(bitrates))

    if not isinstance(bitrates, list):
        bitrates = [bitrates]

    # Download the url with lowest bitrate.
    # Generally it's the default. TODO. Confirm it.
    download_urls = []
    for bitrate in bitrates:
        if bitrate['isDefault']:
            redirect_url = unquote(bitrate['url'])
            download_urls = [redirect_url] + download_urls
        else:
            redirect_url = unquote(bitrate['url'])
            download_urls.append(redirect_url)
    return download_urls

def redirect_and_download(download_urls, filename):
    chunk_size = 1024
    flag = False
    for redirect_url in download_urls:
        # Go through redirection till you reach
        # the final downloadable page.
        r = requests.get(redirect_url, stream=True)
        while r.status_code == 302:
            logger.debug("Redirecting from {}...".format(r.url))
            r = requests.get(r.headers['location'], stream=True)
        logger.debug("Reached the final video page: {}".format(r.url))

        total_length = int(r.headers['content-length'])

        # If total_length is less than 500kB
        # ignore this link.
        if total_length <= 500:
            # Actually we are getting 403: Forbidden error.
            # and hence a total_length = 0
            continue
        
        # Download the video
        # Learnt from http://stackoverflow.com/questions/15644964/python-progress-bar-and-downloads
        logger.info("Downloading {}".format(filename))
        with open(filename, 'wb') as fd:
            content = progress.bar(
                        r.iter_content(chunk_size),
                        expected_size=(total_length/chunk_size + 1)
                      )

            for chunk in content:
                if chunk:
                    fd.write(chunk)
                    fd.flush()
        flag = True
        break

    if not flag:
        logger.warn((
            "Searched through every downloadable URL "
            + "for this embedded video. No content in any URL "
            + "/ we are blocked by them."))
    return flag

def download_video(embedded_video_links, driver, outputfile,
                   has_multiple_parts):
    """
    Extract each url and download
    """

    # Used for naming the files as `part1`, `part2`, ...
    part = 1
    count = 1

    for embedded_link in embedded_video_links:
        # Complete the filename
        filename = outputfile
        if has_multiple_parts:
            filename += '_part_' + str(part)
            part += 1

        if '.flv' in embedded_link:
            filename += '.flv'
        elif '.mkv' in embedded_link:
            filename += '.mkv'
        elif '.mp4' in embedded_link:
            filename += '.mp4'
        else:
            logger.warn(
                ('Could not deduce the video format from "%s".'
                 + ' Marking it as ".mp4"'),
                embedded_link
            )
            filename += '.mp4'

        logger.info("Extracted filename: {}".format(filename))

        download_urls = get_downloadable_links(embedded_link, driver)

        flag = redirect_and_download(download_urls, filename)
        if (not flag) and (not has_multiple_parts):
            if count == len(embedded_video_links):
                logger.warn((
                    "All downloadable links of this final embedded video "
                    + "are empty too. Try downloading using other means."
                ))
            else:
                logger.warn((
                    "All downloadable links of this embedded video "
                    + "are empty. Trying the next embedded video."
                ))
            count += 1
            continue
        elif (not flag) and has_multiple_parts:
            # For videos with multiple parts next tryable 
            # embedded video is in next "tab"
            # and it is best to download all parts from
            # same embedded video provider. Because they
            # will cut videos at different points.

            # get the new embedded_video_links
            # remove the _part_<number>.<mp4> info from filename
            # download_video(embedded_video_links, driver, filename)
            break

        if not has_multiple_parts:
            break

def downloader(
        gogoanime_episode_url, has_multiple_parts=False,
        download_which='all', output_folder='.',
        series=False):

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

    # Initialize the driver
    driver = webdriver.Chrome('/home/abhilash/locallib/chromedriver')
    driver.maximize_window()

    if output_folder[-1] != '/':
        output_folder += '/'

    while True:
        filename = output_folder + gogoanime_episode_url.split("/")[-1]

        embedded_video_links = get_embedded_video_links(gogoanime_episode_url)
        if len(embedded_video_links) == 0:
            logger.info("No video links exist in this page.")
            break

        download_video(embedded_video_links, driver, filename,
                       has_multiple_parts)

        if not series:
            break
        else:
            # We might miss some special episodes if we do it this way.
            # by special we mean either "special/ova/ona" or episodes
            # with different url structure than normal/given.
            # Always check for special episodes and download them individually.
            logger.warn(("We might miss some special episodes. "
                         + "Check for them and download them individually."))

            remurl, epnum = gogoanime_episode_url.rsplit('-', 1)
            gogoanime_episode_url = '-'.join([remurl, str(int(epnum) + 1)])

    driver.quit()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
                description='Download anime episode/movie from gogoanime.',
                formatter_class=argparse.RawTextHelpFormatter
             )

    parser.add_argument(
        'url',
        help='The gogoanime URL which contains the video(s).'
    )

    parser.add_argument(
            '-m', '--has_multiple_parts',
            action='store_true',
            help="""Is the video split in multiple parts ?
(All parts being available in the same URL.)

You only have to give "-m" (without quotes), if
the video has multiple parts. Don't give it, if
the video does not."""
    )

    parser.add_argument(
            '-w', '--download_which',
            default='all',
            help="""Which parts of the video you want to download.
Examples:
    1,3-10,15
    11-20,1-9
    1-100,5-7
    100-87,77-54
1 being the first part and so on.
By default, we download all parts."""
    )

    parser.add_argument(
            '-o', '--output_folder',
            default='.',
            help="""Where do you want to download the video ?
By default, we download to the current folder."""
    )

    parser.add_argument(
            '-s', '--series',
            action='store_true',
            help="""Do you want us to download all the videos
that came after this too ?

You only have to give "-s" (without quotes), if
you want us to. Don't give it otherwise."""
    )

    args = parser.parse_args()
    downloader(
        args.url, args.has_multiple_parts,
        args.download_which, args.output_folder,
        args.series
    )
