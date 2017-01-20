#! /bin/bash
source /usr/local/bin/virtualenvwrapper.sh
workon gogoanime
python core/get_recent_videos.py
deactivate
