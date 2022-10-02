"""This file is used to control in which mode to run the bot based on the config.json file"""
import json

with open('config.json',encoding="utf-8",mode='r') as f:
    mode = json.load(f)["mode"]


if __name__ == '__main__':
    if mode == "debug":
        import bot_debug as Botlib
    elif mode == "prod":
        import bot_prod as Botlib
    else:
        raise Exception("Invalid mode in config.json")
    Botlib.start()
