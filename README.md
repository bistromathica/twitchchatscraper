## About TwitchChatScraper
Monitors multiple streamers on Twitch and saves their chats to an sqlite database 
file through my other project, streamerdb. Options to dump the collected data
in different formats such as .txt files.

## Installation
I don't have a Makefile or any kind of install script because I'm lazy but 
here's the outline:
- Check out both of my projects
    - `git clone https://github.com/bistromathica/streamerdb.git`
    - `git clone https://github.com/bistromathica/twitchchatscraper.git`
- Install and activate Python virtual environment
    - `python3 -m venv .venv`
    - `source .venv/bin/activate`
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

## Examples
Get a point-in-time viewer list snapshot and dump it to a file:

```shell
$ twitchchatscraper getviewerlists
$ twitchchatscraper liststreamers
OurChickenLife
$ twitchchatscraper dumpviewerlists .
$ cat OurChickenLife.txt
```

Scrape configured streamers with verbose output:
```shell
# Add your streamers under "chats" in your .yaml file
# -v option will show chats live. Without it quietly 
# saves chats to the database.
$ twitchchatscraper -v scrape
# background this process or ctrl-c or otherwise open a new terminal
# don't forget `source .venv/bin/activate`
# Dump chat file to current directory
$ twitchchatscraper dumpchat your-streamer-name .
$ cat your-streamer-name.txt
```