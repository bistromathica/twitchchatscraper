## About TwitchChatScraper
Monitors multiple streamers on Twitch and saves their chats to an sqlite database 
file through my other project, streamerdb. Options to dump the collected data
in different formats such as a .txt files.

## Installation
I don't have a Makefile or any kind of install script because I'm lazy but 
here's the outline:
- Check out both of my projects
    - `git checkout https://github.com/bistromathica/streamerdb.git`
    - `git checkout https://github.com/bistromathica/twitchchatscraper.git`
- Install and activate Python virtual environment
    - `python3 -m venv .venv`
    - `source .venv2/bin/activate`
- Install projects and dependencies
    - `pip install ./streamerdb`
    - `pip install ./twitchchatscraper`
- Our browser automation library needs to install browsers
    - `playwright install`
- Make a copy of the sample configuration file and customize. It will look for 
  twitchchatscraper.yaml in your current directory or /etc/twitchchatscraper.yaml.
    - `cp ./twitchchatscraper/conf/twitchchatscraper.yaml .`
- Run `twitchchatscraper` in the same directory as your conf file.

By default, your .sqlite database file will be created as
twitchchatscraper.sqlite in your current directory.
