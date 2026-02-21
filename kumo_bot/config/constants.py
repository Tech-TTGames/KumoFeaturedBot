"""Constant variables used throughout the bot.

This file stores static variables that are used throughout the bot.
This is to keep the code clean and easy to read.
Following the Tickets-Plus pattern for constant organization.
"""
from logging.handlers import RotatingFileHandler
import pathlib

import discord

# Bot version
VERSION = "v1.3.0.0a3"

# Unicode emoji alphabet for reactions
EMOJI_ALPHABET = [
    "\U0001F1E6",  # 🇦
    "\U0001F1E7",  # 🇧
    "\U0001F1E8",  # 🇨
    "\U0001F1E9",  # 🇩
    "\U0001F1EA",  # 🇪
    "\U0001F1EB",  # 🇫
    "\U0001F1EC",  # 🇬
    "\U0001F1ED",  # 🇭
    "\U0001F1EE",  # 🇮
    "\U0001F1EF",  # 🇯
    "\U0001F1F0",  # 🇰
    "\U0001F1F1",  # 🇱
    "\U0001F1F2",  # 🇲
    "\U0001F1F3",  # 🇳
    "\U0001F1F4",  # 🇴
    "\U0001F1F5",  # 🇵
    "\U0001F1F6",  # 🇶
    "\U0001F1F7",  # 🇷
    "\U0001F1F8",  # 🇸
    "\U0001F1F9",  # 🇹
    "\U0001F1FA",  # 🇺
    "\U0001F1FB",  # 🇻
    "\U0001F1FC",  # 🇼
    "\U0001F1FD",  # 🇽
    "\U0001F1FE",  # 🇾
    "\U0001F1FF",  # 🇿
]

# Discord intents configuration
intents = discord.Intents.default()
intents.message_content = True
intents.messages = True

# File Directory
directory = pathlib.Path(__file__).parent.parent.parent
ldir = directory / "logs"
ldir.mkdir(parents=True, exist_ok=True)

# Default logging handler
handler = RotatingFileHandler(filename=ldir / "discord.log", encoding="utf-8", mode="w", backupCount=10, maxBytes=100000)
