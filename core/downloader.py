"""
This function is to be used by a `gogoanime` frequenter
and who can deduce that the anime/movie to be downloaded
has multiple parts.

NOTE: Recently the domain changed from `gogoanime.com` to
`gogoanime.to`. (around last week of August 2016)

Outline:
    An episode page has 2 tabs (generally), each tab containing
    four videos (generally). The four videos are just mirrors of the
    episode we want to download. So, all in all we have 8 mirrors to
    download our video from (generally).

    In case of movies (or episodes which are long), the long video
    is divided into multiple parts of half-an-hour width.
    (Stating the obvious, the number of parts varies by video length)
    So, now each tab acts as one mirror of the required video.
    Generally, we have 4 mirrors (hence 4 tabs).

    Sometimes, some videos can't be loaded and hence can't be downloaded.

TODO: 1. For non-series anime, get all downloadable links
and download from the one with minimum size.
      2. In ubuntu desktop notification, put the `episode title`
that appears in `recent list` or that anime's `episode list` 
instead of modified filename (episode url).
      3. While downloading a whole series of old anime, try to
download the `.5` versions that come in the middle too.
"""
import argparse
import json
import os
import sys

from clint.textui import progress
from lxml import html
import notify2
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
    When we are downloading a series,
    Common url is:
        http://www.gogoanime.com/battery-episode-3
    But, some episodes will have urls like
        http://www.gogoanime.com/battery-episode-3-episode-3
    So, this function if it could not find videos
    in the common url. It will go to previous page
    if it exists and clicks <Next episode>.
    Sometimes, <Next episode> leads to a `movie/special/ova/ona`
    page, so it will skip those and gets the correct url.

    Does this need the `series` flag ? Or can the above procedure
    happen for normal single video downloads too ?
    """

    # Open the episode/ova/ona/special/movie page
    r = requests.get(gogoanime_episode_url)

    if 'gogoanime.com' in gogoanime_episode_url:
        gogoanime_episode_url = gogoanime_episode_url.replace(
            'gogoanime.com', 'gogoanime.to')
    assert gogoanime_episode_url == r.url
    logger.debug("Opened episode page.")

    # Prints out all the video links in the page.
    h = html.fromstring(r.text)
    raw_note = h.xpath("//*[@class='postcontent']/p[1]/img")
    if len(raw_note) > 0:
        # This is not a subbed episode
        logger.info("This is not a subbed video. Not downloading.")
        return []

    embedded_video_links = h.xpath("//*[@class='postcontent']//iframe/@src")
    if len(embedded_video_links) == 0:
        # If there is network issue and the video-available
        # page didn't load. This error occurs. But `scraper`
        # stores in `prev.json` as if the video got downloaded.
        # Should we return false here and do an `if` there ?
        # But but, when we are using this as standalone executable
        # and if we are downloading a series. It will always
        # return false. Hmm, since we have `series` flag, we can
        # check it here....if you want to return true in that case.
        # plus we won't ever use the return value if we are using
        # it as a standalone executable. So, it's fine I guess.
        logger.info("No video links exist in this page.")
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
                   (By.XPATH, "//video")
              ))
    )

    download_url = (
        driver
        .find_element_by_xpath("//video")
        .get_attribute("src")
    )
    return [download_url]

def redirect_and_download(download_urls, filename, no_notification):
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
        if total_length <= 500*chunk_size:
            # Actually we are getting 403: Forbidden error.
            # and hence a total_length = 0
            continue
        
        # Download the video
        # Learnt from http://stackoverflow.com/questions/15644964/python-progress-bar-and-downloads
        logger.info("Downloading {}".format(filename))

        if not no_notification:
            # remove './' at front, replace '-' with ' ', remove '.mp4' at last
            notification_filename = filename.replace('-', ' ')[2:-4]
            n = notify2.Notification("Downloading",
                                     notification_filename)
            n.show()

        with open(filename, 'wb') as fd:
            content = progress.bar(
                        r.iter_content(chunk_size),
                        expected_size=(total_length/chunk_size + 1)
                      )

            for chunk in content:
                if chunk:
                    fd.write(chunk)
                    fd.flush()

        if not no_notification:
            n = notify2.Notification("Download completed",
                                     notification_filename)
            n.show()
            n.close()

        flag = True
        break

    if not flag:
        logger.warn((
            "Searched through every downloadable URL "
            + "for this embedded video. No content in any URL "
            + "/ we are blocked by them."))
    return flag

def download_video(embedded_video_links, driver, outputfile,
                   download_range, has_multiple_parts, no_notification):
    """
    Extract each url and download
    """

    # Used for naming the files as `part1`, `part2`, ...
    part = 1

    for embedded_link in embedded_video_links:
        # download_range is non-empty
        # when series == True too
        # so check for has_multiple_parts == True
        if (has_multiple_parts and
            download_range and
            part not in download_range):
            part += 1
            continue

        # Complete the filename
        filename = outputfile
        if has_multiple_parts:
            filename += '_part_' + str(part)

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

        try:
            download_urls = get_downloadable_links(embedded_link, driver)
        except TimeoutException:
            if has_multiple_parts:
                return False

            # Sometimes, the video does not load, even though other
            # videos in the same page load.
            # TimeoutException occurs, when our scraper could not
            # find any video link to download for that video.
            logger.warn((
                "Failed to download from link number: {}/{}."
                + " Moving forward to the next link."
            ).format(part, len(embedded_video_links)))
            part += 1
            continue

        flag = redirect_and_download(download_urls, filename, no_notification)
        if (not flag) and (not has_multiple_parts):
            if part == len(embedded_video_links):
                logger.warn((
                    "All downloadable links of this final embedded video "
                    + "are empty too. Try downloading using other means."
                ))
            else:
                logger.warn((
                    "All downloadable links of this embedded video "
                    + "are empty. Trying the next embedded video."
                ))
            part += 1
            continue
        elif (not flag) and has_multiple_parts:
            # For videos with multiple parts next tryable 
            # embedded video is in next "tab"
            # and it is best to download all parts from
            # same embedded video provider. Because they
            # might cut videos at different points.
            return False

        if not has_multiple_parts:
            return True
        else:
            part += 1

    return True

def next_episode_url(gogoanime_episode_url):
    # We might miss some special episodes if we do it this way.
    # by special we mean either "special/ova/ona" or episodes
    # with different url structure than normal/given.
    # Always check for special episodes and download them individually.
    logger.warn(("We might miss some special episodes. "
                 + "Check for them and download them individually."))

    # how do you get next episode url
    # you will miss `.5` episodes in between.
    remurl, epnum = gogoanime_episode_url.rsplit('-', 1)
    return '-'.join([remurl, str(int(epnum) + 1)])

def get_download_range(download_which):
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
    #   1-5
    #       - Applicable only when `series` is true.
    #       - Download 1 to 5 episodes.

    # download_range = []
    # if series and download_which != 'all':
    #     if ':' not in download_which:
    #         for rnge in download_which.split(','):
    #             if '-' in rnge:
    #                 a, b = rnge.split('-')
    #                 if a > b:
    #                     a, b = b, a
    #                 download_range.extend(
    #                     [str(x) for x in range(int(float(a)), int(float(b)))]
    #                 )
    #                 if '.' in a:
    #                     download_range.append(a.replace('.', '-'))
    #                 if '.' in b:
    #                     download_range.append(b.replace('.', '-'))
    #             else:
    #                 download_range.append(rnge.replace('.', '-'))




    # Right now, we are solving only the case where
    # we are given:
    #   That they wish to download multiple episodes of an anime
    #   The url from where they want to download.
    #       For example: if they want to download 5, 6 episodes of
    #       a series, they have to give: http://<domain>/<anime>-episode-5
    # we expect them to give:
    #   only 5 and 6 episodes.
    #       we expect them to give 5-6 or 5,6
    #   or in case they want to download 1st, 3rd episodes: 1,3

    # Caution: There should not be spaces.
    # Create a download range
    #   For example: if 1-3,7-9,13 is given
    #       download_range = [1, 2, 3, 7, 8, 9, 13]
    # While the episode url created is within download range
    #   download the episodes that are part of download_range
    #   skip the episodes that are not.
    #   and as soon as it is outside of download range,
    #   break out of the while loop.
    download_range = []  # also means that we have to download all episodes
    for small_range in download_which.split(','):
        nums = small_range.split('-')
        if len(nums) == 1 and nums[0] != 'all':
            download_range.append(int(nums[0]))
        elif len(nums) == 2:
            download_range.extend(range(int(nums[0]), int(nums[1]) + 1))
    download_range.sort()

    logger.debug('{}'.format(download_range))
    return download_range

def get_num_tabs(gogoanime_episode_url):
    r = requests.get(gogoanime_episode_url)
    h = html.fromstring(r.text)
    tabs = h.xpath("//*[@class='tabpadding']//a")
    return len(tabs) + 1

def downloader(
        gogoanime_episode_url, driver, has_multiple_parts=False,
        download_which='all', output_folder='.',
        series=False, no_notification=False):

    if not no_notification:
        notify2.init("Download anime")

    download_range = get_download_range(download_which)

    while True:
        # Assuming, if the video has multiple parts
        # we will be asked to download all parts.
        # i.e., download_which == 'all'
        #
        # Also assuming, we will not be asked to
        # download a series of multi-part videos.

        if download_range and series:
            ep_num = int(gogoanime_episode_url.rsplit('-', 1)[1])
            if ep_num not in download_range:

                # download_range is in increasing order
                if ep_num > download_range[-1]:
                    break

                gogoanime_episode_url = next_episode_url(gogoanime_episode_url)
                continue

        logger.info("Trying to download video from: {}"
                    .format(gogoanime_episode_url))

        filename = os.path.join(output_folder,
                                gogoanime_episode_url.rsplit("/", 1)[1])

        num_tabs = get_num_tabs(gogoanime_episode_url)
        logger.debug("Number of tabs: {}".format(num_tabs))

        success = False
        for tabcount in range(num_tabs):
            if tabcount == 0:
                url = gogoanime_episode_url
            else:
                url = gogoanime_episode_url + '/' + str(tabcount + 1)

            try:
                embedded_video_links = get_embedded_video_links(url)

                # This happens either when we find that this video is raw
                # or if there are no videos in this page.
                # Don't pursue either this or next-in-line videos.
                if len(embedded_video_links) == 0:
                    series = False
                    break

                success = download_video(
                    embedded_video_links, driver, filename,
                    download_range, has_multiple_parts, no_notification
                )

                if success:
                    break

                logger.warn(
                    "Could not download from this tab. Trying next tab."
                )
            except requests.exceptions.ConnectionError:
                logger.warn("Could not connect to this tab. Trying next tab.")

        if not success:
            break

        if not series:
            break

        gogoanime_episode_url = next_episode_url(gogoanime_episode_url)

    return success

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

    parser.add_argument(
        '-n', '--no_notification',
        action='store_true',
        help="""Do you want us to NOT notify you whenever
download of your anime started and completed ?

Give "-n" (without quotes), if you want us NOT to.
Don't give it otherwise."""
    )

    args = parser.parse_args()

    # Initialize the driver
    # TODO: Driver opens a browser window always which is obtrusive
    # to whatever task the user is doing. Can we run it in the 
    # background or just use `requests` package or use 'headless' browser ?
    home = os.path.expanduser("~")
    driver = webdriver.Chrome(os.path.join(home, 'locallib/chromedriver'))
    driver.maximize_window()

    downloader(
        args.url, driver, args.has_multiple_parts,
        args.download_which, args.output_folder,
        args.series, args.no_notification
    )

    driver.quit()

