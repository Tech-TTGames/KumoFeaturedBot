"""This file is used to control in which mode to run the bot based on the config.json file"""
import json
import logging

try:
    with open("config.json", encoding="utf-8") as f:
        MODE = json.load(f)["mode"]
except FileNotFoundError:
    logging.critical("config.json not found. Entering setup mode.")
    MODE = "setup"
except json.decoder.JSONDecodeError:
    logging.critical("config.json could not be read. Entering setup mode.")
    MODE = "setup"

if __name__ == "__main__":
    if MODE == "debug":
        import bot_debug as Botlib
    elif MODE == "prod":
        import bot_prod as Botlib
    else:
        import bot_setup as Botlib

        logging.critical(
            "Invalid or not found mode in config.json. Entering setup mode."
        )
        MODE = "setup"
    Botlib.start()
