"""This is the main file for the bot in debug mode.
It contains a limited version of the bot's commands and events.
This file now uses the modular structure.
"""
from kumo_bot.debug_bot import DebugBot


def start():
    """Starts the bot."""
    bot = DebugBot()
    bot.run_bot()


if __name__ == "__main__":
    start()
