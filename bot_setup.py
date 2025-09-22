"""Bot setup module. Runs if config.json is not found.
This file now uses the modular structure.
"""
from kumo_bot.setup_bot import SetupBot


def start():
    """Starts the bot."""
    bot = SetupBot()
    bot.run_bot()


if __name__ == "__main__":
    start()
