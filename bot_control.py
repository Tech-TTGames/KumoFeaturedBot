"""This file is used to control in which mode to run the bot based on the config.json file"""
import json

with open('config.json',encoding="utf-8") as f:
    config = json.load(f)


if __name__ == '__main__':
    if config["mode"] == "debug":
        import bot_debug as Botlib
    elif config["mode"] == "prod":
        import bot_prod as Botlib
    else:
        raise Exception("Invalid mode in config.json")
    Botlib.start()
