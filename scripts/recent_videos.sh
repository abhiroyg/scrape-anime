#! /bin/bash
source /usr/local/bin/virtualenvwrapper.sh
workon gogoanime_py3
python core/get_recent_videos.py
deactivate
