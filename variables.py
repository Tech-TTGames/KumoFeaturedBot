"""Declare variables that aren't changed between debug and production"""
import json
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from typing import List, Optional, Union

import discord
from discord.ext import commands

# v[major].[minor].[release].[build]
VERSION = "v1.2.0.0"
EMOJI_ALPHABET = [
    "\U0001F1E6",
    "\U0001F1E7",
    "\U0001F1E8",
    "\U0001F1E9",
    "\U0001F1EA",
    "\U0001F1EB",
    "\U0001F1EC",
    "\U0001F1ED",
    "\U0001F1EE",
    "\U0001F1EF",
    "\U0001F1F0",
    "\U0001F1F1",
    "\U0001F1F2",
    "\U0001F1F3",
    "\U0001F1F4",
    "\U0001F1F5",
    "\U0001F1F6",
    "\U0001F1F7",
    "\U0001F1F8",
    "\U0001F1F9",
    "\U0001F1FA",
    "\U0001F1FB",
    "\U0001F1FC",
    "\U0001F1FD",
    "\U0001F1FE",
    "\U0001F1FF",
]

intents = discord.Intents.default()
intents.message_content = True  # pylint: disable=assigning-non-slot
intents.messages = True  # pylint: disable=assigning-non-slot
handler = RotatingFileHandler(filename="discord.log",
                              encoding="utf-8",
                              mode="w",
                              backupCount=10,
                              maxBytes=100000)


class Secret:
    """Class for secret.json management"""

    def __init__(self) -> None:
        self._file = "secret.json"
        with open(self._file, encoding="utf-8") as secret_f:
            self._secret = json.load(secret_f)
        self.token = self._secret["token"]

    def __str__(self) -> str:
        return "[OBFUSCATED]"

    def __dict__(self) -> dict:
        return self._secret


class Config:
    """Class for convenient config access"""

    def __init__(self, bot: commands.Bot) -> None:
        self._file = "config.json"
        self.armed = False
        with open(self._file, encoding="utf-8") as config_f:
            self._config = json.load(config_f)
        self._bt = bot
        self.closetime_timestamp = self._config["closetime"]

    def __dict__(self) -> dict:
        return self._config

    def update(self) -> None:
        """Update the config.json file to reflect changes"""
        with open(self._file, encoding="utf-8", mode="w") as config_f:
            json.dump(self._config, config_f, indent=4)
            config_f.truncate()

    # GETTERS AND SETTERS FOLLOW

    @property
    def mode(self) -> str:
        """Gets current mode"""
        return self._config["mode"]

    @mode.setter
    def mode(self, mode: str) -> None:
        self._config["mode"] = mode
        self.update()

    @property
    def prefix(self) -> str:
        """Gets current prefix"""
        return self._config["prefix"]

    @prefix.setter
    def prefix(self, prefix: str) -> None:
        self._config["prefix"] = prefix
        self.update()

    @property
    def guild(self) -> discord.Guild:
        """Gets guild from config"""
        tmp = self._bt.get_guild(self._config["guild"])
        if tmp is None:
            raise ValueError("Guild not found")
        return tmp

    @guild.setter
    def guild(self, guild: discord.Guild) -> None:
        self._config["guild"] = guild.id
        self.update()

    @property
    def channel(self) -> Union[discord.TextChannel, discord.Thread]:
        """Gets the channel from config"""
        tmp = self._bt.get_channel(self._config["channel"])
        if tmp is None:
            raise ValueError("Channel not found")
        if isinstance(tmp, (discord.TextChannel, discord.Thread)):
            return tmp
        raise ValueError("Channel is not a text channel or thread")

    @channel.setter
    def channel(self, channel: Union[discord.TextChannel,
                                     discord.Thread]) -> None:
        self._config["channel"] = channel.id
        self.update()

    @property
    def role(self) -> discord.Role:
        """Gets botrole from config"""
        tmp = self.guild.get_role(self._config["role"])
        if tmp is None:
            raise ValueError("Role not found")
        return tmp

    @property
    def role_id(self) -> int:
        """Gets botrole from config"""
        if self._config["role"] is None:
            raise ValueError("Role not set")
        return self._config["role"]

    @role.setter
    def role(self, rle: discord.Role) -> None:
        self._config["role"] = rle.id
        self.update()

    @property
    def mention(self) -> discord.Role:
        """Gets vote mention from config"""
        tmp = self.guild.get_role(self._config["mention"])
        if tmp is None:
            raise ValueError("Role not found")
        return tmp

    @mention.setter
    def mention(self, role: discord.Role) -> None:
        self._config["mention"] = role.id
        self.update()

    @property
    async def lastvote(self) -> Optional[discord.Message]:
        """Gets last vote's message from config"""
        try:
            if self._config["lastvote"] is None:
                return None
            tmp = await self.channel.fetch_message(self._config["lastvote"])
            if tmp is None:
                raise ValueError("Message not found")
            return tmp
        except KeyError:
            return None

    @lastvote.setter
    def lastvote(self, msg: discord.Message) -> None:
        self._config["lastvote"] = msg.id
        self.update()

    @property
    async def lastwin(self) -> Optional[discord.Message]:
        """Gets last win's message from config"""
        try:
            if self._config["lastwin"] is None:
                return None
            tmp = await self.channel.fetch_message(self._config["lastwin"])
            if tmp is None:
                raise ValueError("Message not found")
            return tmp
        except KeyError:
            return None

    @lastwin.setter
    def lastwin(self, msg: discord.Message) -> None:
        self._config["lastwin"] = msg.id
        self.update()

    @property
    def closetime(self) -> Optional[datetime]:
        """Gets time to close the running vote on"""
        try:
            if self._config["closetime"] is None:
                return None
            return datetime.fromtimestamp(self._config["closetime"],
                                          tz=timezone.utc)
        except KeyError:
            return None

    @closetime.setter
    def closetime(self, time: Optional[datetime]) -> None:
        if time is None:
            self._config["closetime"] = None
        else:
            self._config["closetime"] = time.timestamp()
        self.update()

    @property
    def vote_running(self) -> bool:
        """Checks if a vote is running"""
        try:
            return self._config["voterunning"]
        except KeyError:
            return False

    @vote_running.setter
    def vote_running(self, running: bool) -> None:
        self._config["voterunning"] = running
        self.update()

    @property
    def blacklist(self) -> List[int]:
        """Gets blacklist"""
        try:
            return self._config["blacklist"]
        except KeyError:
            return []

    @blacklist.setter
    def blacklist(self, blacklist: List[int]) -> None:
        """Adds or removes a user from the blacklist"""
        self._config["blacklist"] = blacklist
        self.update()

    @property
    def owner_role(self) -> Union[str, int]:
        """Gets the owner role"""
        try:
            return self._config["owner_role"]
        except KeyError:
            return "Administrator"

    @property
    def vote_count_mode(self) -> int:
        """Gets vote count mode"""
        try:
            return self._config["vote_count_mode"]
        except KeyError:
            return 0

    @vote_count_mode.setter
    def vote_count_mode(self, mode: int) -> None:
        self._config["vote_count_mode"] = mode
        self.update()

    @property
    def democracy(self) -> list[discord.Member, None] | list[None]:
        """Get democracy-privileged users"""
        try:
            ids = self._config["democracy"]
            return [self.guild.get_member(id_) for id_ in ids]
        except KeyError:
            return [None]
