from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import WebDriverWait


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
