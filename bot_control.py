"""This file is used to control in which mode to run the bot based on the config.json file"""
import json
import logging

try:
    with open('config.json',encoding="utf-8",mode='r') as f:
        MODE = json.load(f)["mode"]
except FileNotFoundError:
    logging.critical("config.json not found. Entering setup mode.")
    MODE = "setup"

if __name__ == '__main__':
    if MODE == "setup":
        import bot_setup as Botlib
    elif MODE == "debug":
        import bot_debug as Botlib
    elif MODE == "prod":
        import bot_prod as Botlib
    else:
        raise Exception("Invalid mode in config.json")
    Botlib.start()
