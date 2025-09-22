"""Download utilities for fanfiction and novels."""
import asyncio
import functools
import io
import logging
import re

import discord
from fanficfare import cli, exceptions


async def fetch_download(url: str) -> discord.File:
    """Fetches a file from an url.

    Args:
        url: The url to fetch the file from.
    """
    loop = asyncio.get_event_loop()
    string_io = io.StringIO()
    log_handler = logging.StreamHandler(string_io)
    cli.logger.addHandler(log_handler)
    options, _ = cli.mkParser(calibre=False).parse_args(["--non-interactive", "--force", "-o is_adult=true"])
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
        cli.logger.removeHandler(log_handler)
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
    raise Exception(
        "FanFicFare failed to download. Due to security issues lightnovel-crawler is currently unsupported.")
