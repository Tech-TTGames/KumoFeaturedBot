import subprocess
import json

with open('config.json') as f:
    config = json.load(f)

if __name__ == '__main__':
    if config["mode"] == "debug":
        subprocess.call(["python3", "BotMaintance.py"])
    elif config["mode"] == "prod":
        subprocess.call(["python3", "Bot.py"])
    else:
        raise Exception("Invalid mode in config.json")