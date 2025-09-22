"""Download utilities for fanfiction and novels."""
import asyncio
import functools
import io
import logging
import os
import re
from requests import get

import discord
from fanficfare import cli, exceptions
from lncrawl.core import app


async def fetch_download(url: str, application: app.App, log_stuff) -> discord.File:
    """Fetches a file from an url.

    Args:
        url: The url to fetch the file from.
        application: The lightnovel-crawler application instance.
        log_stuff: The logger instance.
    """
    loop = asyncio.get_event_loop()
    string_io = io.StringIO()
    log_handler = logging.StreamHandler(string_io)
    log_stuff.addHandler(log_handler)
    options, _ = cli.mkParser(calibre=False).parse_args(
        ["--non-interactive", "--force", "-o is_adult=true"])
    cli.expandOptions(options)
    try:
        await loop.run_in_executor(
            None,
            functools.partial(
                cli.dispatch,
                options,
                [url],
                warn=log_stuff.warn,  # type: ignore
                fail=log_stuff.critical,  # type: ignore
            ),
        )
    except exceptions.UnknownSite:
        filename = None
    else:
        logread = string_io.getvalue()
        string_io.close()
        log_stuff.removeHandler(log_handler)
        log_handler.close()
        regexed = re.search(r"Successfully wrote '(.*)'", logread)
        if regexed:
            filename = regexed.group(1)
        else:
            filename = None
            logging.info("Failed to download. IO:\n %s", logread)
    if isinstance(filename, str):
        logging.info("Successfully downloaded %s", filename)
        return discord.File(fp=filename)
    logging.info("FanFicFare failed to download %s, falling back to lightnovel-crawler!", url)
    application.user_input = url.strip()
    await loop.run_in_executor(None, application.prepare_search)
    await loop.run_in_executor(None, application.get_novel_info)

    os.makedirs(application.output_path, exist_ok=True)
    application.chapters = application.crawler.chapters[:]
    logging.info("Downloading cover: %s", application.crawler.novel_cover)
    img = get(application.crawler.novel_cover, timeout=60)
    with open(os.path.join(application.output_path, "cover.jpg"), "wb") as f:
        f.write(img.content)
    application.book_cover = os.path.join(application.output_path, "cover.jpg")

    logging.info("Downloading chapters...")
    await loop.run_in_executor(None, application.start_download)
    await loop.run_in_executor(None, application.bind_books)
    logging.info("Bound books.")
    filepath = os.path.join(application.output_path, "epub",
                            application.good_file_name + ".epub")
    return discord.File(fp=filepath)