"""This file is used to control in which mode to run the bot based on the config.json file"""
import json
import logging
import os

from lncrawl.core import proxy


def get_mode():
    """Determine which mode to run the bot in."""
    try:
        with open("config.json", encoding="utf-8") as f:
            mode = json.load(f)["mode"]
        return mode
    except FileNotFoundError:
        logging.critical("config.json not found. Entering setup mode.")
        return "setup"
    except json.decoder.JSONDecodeError:
        logging.critical("config.json could not be read. Entering setup mode.")
        return "setup"


def start_bot():
    """Start the appropriate bot based on the mode."""
    mode = get_mode()
    
    if mode == "debug":
        from kumo_bot.debug_bot import DebugBot
        bot = DebugBot()
        bot.run_bot()
    elif mode == "prod":
        from kumo_bot.bot import KumoBot
        os.environ["use_proxy"] = "auto"
        proxy.start_proxy_fetcher()
        try:
            bot = KumoBot()
            bot.run_bot()
        finally:
            proxy.stop_proxy_fetcher()
    else:
        from kumo_bot.setup_bot import SetupBot
        logging.critical("Invalid or not found mode in config.json. Entering setup mode.")
        bot = SetupBot()
        bot.run_bot()


if __name__ == "__main__":
    start_bot()
