## Todo
### Features
* run the `playwright install` command automatically 
* database pruning functions
* get viewer lists while scraping chat
* username appearances or chats query
* monitor bits donations or subscriptions
* monitor raids
* monitor polls 
* monitor redeems
* parse replies
* record as HTML and generate HTML that looks like Twitch chat
* recursive viewerlist scraping, need to record "nobody found in list"
* have option to export to local timezone (say this in the output)
### Bugs
* outgoing raids cause it to think new streamer is original streamer
* chat sometimes "stops" after a while 

## Done
* dump all as text command for grepping
* scrape_chat uses 0.5 second polling and always get the last chat message in the list.
  this means it both uses too much CPU and also will miss when more than one message
  comes in at the same time. this sucks. 