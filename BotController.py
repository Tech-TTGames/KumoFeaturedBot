import json

with open('config.json') as f:
    config = json.load(f)

if __name__ == '__main__':
    if config["mode"] == "debug":
        import BotMaintance as Botlib
    elif config["mode"] == "prod":
        import BotGeneral as Botlib
    else:
        raise Exception("Invalid mode in config.json")
    Botlib.start()