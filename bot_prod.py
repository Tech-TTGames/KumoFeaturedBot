"""This is the main file for the bot.
It contains a full version of the bot's commands and events.
This file now uses the modular structure.
"""
import os
from lncrawl.core import proxy

from kumo_bot.bot import KumoBot


def start():
    """Starts the bot."""
    bot = KumoBot()
    bot.run_bot()


if __name__ == "__main__":
    os.environ["use_proxy"] = "auto"
    proxy.start_proxy_fetcher()
    start()
    proxy.stop_proxy_fetcher()