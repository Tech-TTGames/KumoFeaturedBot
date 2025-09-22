"""This file is used to control in which mode to run the bot based on the config.json file"""
import json
import logging


def get_mode():
    """Determine which mode to run the bot in."""
    try:
        with open("config.json", encoding="utf-8") as f:
            bmode = json.load(f)["mode"]
        return bmode
    except FileNotFoundError:
        logging.critical("config.json not found. Entering setup mode.")
        return "setup"
    except json.decoder.JSONDecodeError:
        logging.critical("config.json could not be read. Entering setup mode.")
        return "setup"


if __name__ == "__main__":
    mode = get_mode()

    if mode == "debug":
        from kumo_bot.debug_bot import DebugBot

        bot = DebugBot()
    elif mode == "prod":
        from kumo_bot.bot import KumoBot

        bot = KumoBot()
    else:
        from kumo_bot.setup_bot import SetupBot

        logging.critical("Invalid or not found mode in config.json. Entering setup mode.")
        bot = SetupBot()
    bot.run_bot()
