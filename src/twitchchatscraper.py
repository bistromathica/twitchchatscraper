"""Twitch scraping functions using Playwright.
Gets the list of viewers from each stream.
"""
import sys
import signal
from playwright.async_api import async_playwright, Browser
import asyncio
import logging
from streamerdb import Streamer, Username, ViewerlistAppearance, ChatMessage, Tortoise
import configuration
import click
from datetime import datetime


should_stop = asyncio.Event()
http_semaphore = None  # Gets defined later


async def twitch_message_to_text(parent):
    body = ""
    for element in await parent.query_selector_all('span[data-a-target=chat-line-message-body] > *'):
        txt = await element.inner_text()
        if txt:
            body += txt
        else:
            img = await element.query_selector('img.chat-image')
            if img:
                body += await img.get_attribute('alt')
    return body


async def parse_twitch_message(element):
    username = await element.get_attribute('data-a-user')
    body = await twitch_message_to_text(element)
    # await element.evaluate("element => element.setAttribute('data-parsed', 'true')")
    await element.evaluate("element => element.remove()")
    return username, body


async def scrape_chat(browser: Browser, streamer: Streamer):
    """
    div.stream-chat is the parent element for the chat.
    div.chat-line__message is the elements for each message in chat
    """
    page = await browser.new_page()
    logging.debug('opening streamer chat %s', streamer)
    async with http_semaphore:
        await page.goto(await streamer.get_chat_url())
    logging.debug('opened')
    message_locator = page.locator('div.chat-line__message').first

    while not should_stop.is_set():
        await message_locator.wait_for(timeout=0)
        yield await parse_twitch_message(await message_locator.element_handle())
        await asyncio.sleep(0.01)  # Be nice to CPU


async def process_chat(browser: Browser, streamer: Streamer):
    async for username, body in scrape_chat(browser, streamer):
        viewer, created = await Username.get_or_create(username=username)
        msg = await ChatMessage.create(streamer=streamer, viewer=viewer, message=body)
        logging.info("msg: %s %s %s", await streamer.username, username, body)


async def get_viewer_list(browser: Browser, streamer: Streamer):
    """Clicks Users In Chat button and gets every div[role=listitem]"""
    logging.debug("getting viewer list for %s", streamer)
    page = await browser.new_page()
    async with http_semaphore:
        await page.goto(await streamer.get_chat_url())
    button = page.locator('[aria-label="Users in Chat"]')
    await button.wait_for()
    await button.click()
    logging.debug("button clicked for %s", streamer)
    viewers_list = page.locator('div.chat-viewers__list')
    await viewers_list.wait_for()
    viewer_locator = viewers_list.locator('button.chat-viewers-list__button')
    await asyncio.sleep(0.5)  # TODO: Kinda sloppy, should wait properly
    logging.debug('viewer_locator elements %s', await viewer_locator.count())
    for n in range(await viewer_locator.count()):
        viewer = await viewer_locator.nth(n).get_attribute('data-username')
        yield viewer
    await page.close()


async def process_streamer(browser: Browser, streamer: Streamer):
    now = datetime.now()
    async for viewer_username in get_viewer_list(browser, streamer):
        # I don't like this await evaluating every time even if not logging
        logging.info("%s: %s", await streamer.username, viewer_username)
        viewer, created = await Username.get_or_create(username=viewer_username)
        await ViewerlistAppearance.create(viewer=viewer, streamer=streamer, when=now)


async def get_streamers(conf):
    streamers = []
    for chat in conf.chats:
        username, created = await Username.get_or_create(username=chat)
        streamer, created = await Streamer.get_or_create(username=username, platform='twitch')
        streamers.append(streamer)
    return streamers


async def _scrape(conf, task):
    loop = asyncio.get_running_loop()
    loop.add_signal_handler(signal.SIGINT, stop_all)
    loop.add_signal_handler(signal.SIGTERM, stop_all)
    await Tortoise.init(db_url=conf.db_url, modules={'models': ['streamerdb']})
    try:
        await Tortoise.generate_schemas(safe=True)
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=conf.headless)
            streamers = await get_streamers(conf)
            await asyncio.gather(*(task(browser, streamer) for streamer in streamers))
            await browser.close()
    finally:
        await Tortoise.close_connections()


async def _query(conf, task):
    loop = asyncio.get_running_loop()
    loop.add_signal_handler(signal.SIGINT, stop_all)
    loop.add_signal_handler(signal.SIGTERM, stop_all)
    await Tortoise.init(db_url=conf.db_url, modules={'models': ['streamerdb']})
    try:
        await Tortoise.generate_schemas(safe=True)
        return await task
    finally:
        await Tortoise.close_connections()


async def _allstreamers():
    """Just get a list of Streamer.username"""
    r = await Streamer.all().values_list("username__username")
    return [x[0] for x in r]


async def _dumpviewerlists(directory):
    """Creates one text file per streamer and writes each viewer list snapshot."""
    for streamer in await Streamer.all():
        username = await streamer.username
        with open(f"{directory}/{username}.txt", "w") as file:
            for time, in await username.viewer_appearances.all().distinct().values_list('when'):
                file.write(f"{time}\n")
                file.write("    ")
                async for viewer_username, in username.viewer_appearances.filter(when=time).values_list('viewer__username'):
                    file.write(viewer_username+', ')
                file.write("\n")


async def _dumpchat(username, directory):
    """Dumps all saved chats for a given streamer into a text file in a given directory."""
    streamer = await Streamer.get(username__username=username)
    with open(f"{directory}/{username}.txt", "w") as file:
        last_date = None
        q = streamer.chat_messages.filter().order_by('created')
        async for created, author, message in q.values_list('created', 'viewer__username', 'message'):
            date = created.date().strftime("%Y-%m-%d")
            if last_date != date:
                file.write(f"{date}\n")
                file.write("-"*20+'\n')
                last_date = date
            file.write(f"[{created.strftime('%H:%M')}] <{author}> {message}\n")


async def _dumpall(timestamps=True):
    """Dumps all chats in database."""
    async for created, streamer, author, message in (
            ChatMessage.all().order_by('created')
            .values_list('created', 'streamer__username__username', 'viewer__username', 'message')):
        if timestamps:
            print(f"[{streamer}] {created.strftime('%Y-%m-%d %H:%M:%S')} <{author}> {message}")
        else:
            print(f"[{streamer}] <{author}> {message}")


@click.group()
@click.option('--verbose', '-v', is_flag=True, default=[], multiple=True, help='Verbose output')
@click.option('--config', '-c', default=None, help='Custom config file location')
@click.pass_context
def cli(ctx, verbose, config):
    global http_semaphore

    loglevel = len(verbose)
    if loglevel > 1:
        logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)
    elif loglevel:
        logging.basicConfig(level=logging.INFO, stream=sys.stdout)

    ctx.ensure_object(dict)
    ctx.obj['config'] = configuration.get(config)
    http_semaphore = asyncio.Semaphore(ctx.obj['config'].concurrency)  # limiter for concurrent http requests


def stop_all(*args):
    should_stop.set()


@cli.command(help='Start the scraper for the configured Twitch chats.')
@click.pass_context
def scrape(ctx):
    asyncio.run(_scrape(ctx.obj['config'], process_chat))


@cli.command(help='Save the viewer list for the configured Twitch chats and exit.')
@click.pass_context
def getviewerlists(ctx):
    asyncio.run(_scrape(ctx.obj['config'], process_streamer))


@cli.command(help='List all streamers in database.')
@click.pass_context
def liststreamers(ctx):
    usernames = asyncio.run(_query(ctx.obj['config'], _allstreamers()))
    print('\n'.join(usernames))


@cli.command(help='Dump the viewer lists into text files, one per streamer.')
@click.argument('directory')
@click.pass_context
def dumpviewerlists(ctx, directory):
    asyncio.run(_query(ctx.obj['config'], _dumpviewerlists(directory)))


@cli.command(help='Dump the entire saved chats of a streamer into a text file.')
@click.argument('username')
@click.argument('directory')
@click.pass_context
def dumpchat(ctx, username, directory):
    asyncio.run(_query(ctx.obj['config'], _dumpchat(username, directory)))


@cli.command(help='Dump all chats to stdout for grepping')
@click.option("--no-timestamps", is_flag=True, help="Don't print timestamps in output", )
@click.pass_context
def dumpall(ctx, no_timestamps):
    asyncio.run(_query(ctx.obj['config'], _dumpall(not no_timestamps)))
