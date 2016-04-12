# scrape-anime
This program scrapes the recent anime/movies uploaded in gogoanime.com website.

Disclaimer:
It will print a warning if it misses some - though it won't give you how many it missed. So, if it misses you are on your own. Sorry :(

Current:
Downloads the first episode in the "recent episodes" list, unless already downloaded.

TODO:
1. Have an independent tracker which tracks gogoanime.com website every 15 minutes for recent episodes.
1. Write a log-reader which reads the output of the above tracker (whenever scheduled to) and downloads the anime/movie.
1. Give option to download only sub/dub/raw
1. Give option to download only anime/ova/movie/...
1. Give option to download only those series user is interested in.
1. Give option to specify gap between two downloads, in case of parallel downloads.
1. Give option to pause and resume downloads (can't at my current level)
1. Run in windows (integrating with IDM) (above and beyond current capability)
