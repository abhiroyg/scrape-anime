# scrape-anime
This program scrapes/downloads and stores the recent anime/movies uploaded in gogoanime.com website.

Disclaimer:
It will print a warning if it misses some - though it won't give you how many it missed. So, if it misses you are on your own. Sorry :(

Current:
Downloads the first episode in the "recent episodes" list, unless already downloaded.

TODO:
1. Have an independent tracker which tracks gogoanime.com website every 15 minutes for recent episodes.
1. Write a log-reader which reads the output of the above tracker (whenever scheduled to) and downloads the anime/movie.
1. Give option to download only sub/dub/raw/preview
1. Give option to download only anime/ova/movie/...
1. Give option to download only those series user is interested in.
1. Give option to specify gap between two downloads, in case of parallel downloads.
1. Give option to choose naming convention for downloaded videos.
1. Give option to pause and resume downloads (can't at my current level)
1. Run in windows (integrating with IDM) (above and beyond current capability)

CURRENT VISION: (04/07/2016)
1. Check the website at some configurable interval and notify whenever you encounter new episodes.

    1. if the interval is large, we might miss some episodes
    1. and if it is small, we might overload the system
    1. by default, the interval is 1 hr. No particular reason for choosing this.
    1. By default, it will search for all anime but you can configure it to search for only some anime.
    1. This tracker, need not run continuously...but whenever it is run...it is a standalone.
    1. But, if notify system is there, then the notified program should be run continuously, to get notified.
    1. If no notification, just store the downloadble links in db.
    1. Whenever the notified system runs, it will check db and downloads not already downloaded stuff.

1. We can improve the above system: 

    1. if we have to search only for a few anime, by noting down the time of release
and searching only at that time. Negative point will be that, the anime might not get
release at that time. We have to resort to interval again. Implementing this switch can
be a pain.

    1. And say if we downloaded 5th episode last time but are now downloading 8th episode,
    i.e., if we missed some episodes because of the check-website-interval being large, download
    the in-between episodes too.
    1. But we have to note that, the episode url can be a bit of a problem. If the normal way does not work,
    go to the last 5th episode's url and from there get the 6th episode's url. And then go to the 6th episode's
    url and from there get the 7th episode's url.
    1. There's one more problem in this improvement i.e., we won't know if it is a sub/dub/raw/preview....
        
        1. just found out that preview(s) have a three line format (e.g., "....HERE IS THE PREVIEW...")
        1. raws have a "This is a RAW version..." strip.
        1. There's no guarantee that old episodes have the same format for preview/raw.
        1. Dunno how to differentiate dubs/subs. But, if the previous episodes are subs then we can assume
        future episodes will be subs and viceversa.

1. We need to store all the to-be-downloaded links in database with a flag saying if it got downloaded or not.
    We also need a mutex while accessing db.
    We might need db to get only those entries with downloaded-flag false.

1. When we get notified of presence of new anime and their downloadable links...we start downloading them
parallely.....how many in parallel is configurable....but if too many in parallel, we consume so much
system resources....if no parallelism i.e., if serial, it takes time to download all of them.

    1. By default, we will have 3 parallel threads, no particular reason for choosing this. Just that,
    I have been, somehow, downloading stuff at this rate so far.
    1. If we get notified of the presence and the downloadable links....we don't need db with downloaded-flag.
    1. We just need a file to store already downloaded episodes, download start date, download end date, sub/dub/raw flag,
    anime/ova/movie flag, which anime, anime start date (if possible), anime end date (if possible), folder in which
    we are storing the anime, do we have to create a backup for permanent storage (not needed may be) or is permanently
    stored (which tells if the user liked the anime or not), in which device we have to store permanently and in which 
    folder (too advanced because we have to show a popup whenever the device is inserted to tell if the user want to
    store the not already backed up anime), when did the last backup took place - start and end datetime, alternative
    name(s) for the anime.

1. Give provision to search for old anime and if they are available to download them.
    
    1. Return the results of the search and give provision to retry search again.
    1. Give provision to select one of the episodes/series so that you can start downloading them.
    1. Also give provision to download only one episode and not the entire series with above option.
    1. Also give provision to multi-select episodes and download them.
    1. If multi-selected from different anime, ask if they want to download entire series for each of 
    them or just the episodes.

1. Give provision to notify whenever there is a new anime. And if interested, to start downloading them whenever
a new episode is available.
    
    1. This whenever can be done by setting an interval like every 5 days or so.
    1. Problem comes: when to stop downloading/searching for new episodes of this anime. One thing is to put a
    threshold like if no new episode for 30 days. Don't download.
    1. We also have to give provision to say, if ova gets released for the same anime (say, after 2 years),
    we should recognize it and store the downloaded stuff in same folder, may be a different sub-folder.
    1. But, if the folder gets deleted, since we store in db the folder, we can reproduce the folder name.

