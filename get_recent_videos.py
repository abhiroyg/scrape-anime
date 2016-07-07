import lxml
import requests

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
