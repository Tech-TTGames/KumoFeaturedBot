"""Configuration management classes for KumoFeaturedBot.

This module contains the Secret and Config classes for managing
bot configuration and secrets, following the Tickets-Plus pattern.
"""
import json
from datetime import datetime, timezone
from typing import List, Optional, Union

import discord
from discord.ext import commands


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
        if self._config.get("lastvote", None) is None:
            return None
        tmp = await self.channel.fetch_message(self._config["lastvote"])
        if tmp is None:
            raise ValueError("Message not found")
        return tmp

    @lastvote.setter
    def lastvote(self, msg: discord.Message) -> None:
        self._config["lastvote"] = msg.id
        self.update()

    @property
    async def lastwin(self) -> Optional[discord.Message]:
        """Gets last win's message from config"""
        if self._config.get("lastwin", None) is None:
            return None
        tmp = await self.channel.fetch_message(self._config["lastwin"])
        if tmp is None:
            raise ValueError("Message not found")
        return tmp

    @lastwin.setter
    def lastwin(self, msg: discord.Message) -> None:
        self._config["lastwin"] = msg.id
        self.update()

    @property
    def closetime(self) -> Optional[datetime]:
        """Gets time to close the running vote on"""
        if self._config.get("closetime", None) is None:
            return None
        return datetime.fromtimestamp(self._config["closetime"],
                                      tz=timezone.utc)

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
        return self._config.get("voterunning", False)

    @vote_running.setter
    def vote_running(self, running: bool) -> None:
        self._config["voterunning"] = running
        self.update()

    @property
    def blacklist(self) -> List[int]:
        """Gets blacklist"""
        return self._config.get("blacklist", [])

    @blacklist.setter
    def blacklist(self, blacklist: List[int]) -> None:
        """Adds or removes a user from the blacklist"""
        self._config["blacklist"] = blacklist
        self.update()

    @property
    def owner_role(self) -> Union[str, int]:
        """Gets the owner role"""
        return self._config.get("owner_role", "Administrator")

    @property
    def vote_count_mode(self) -> int:
        """Gets vote count mode"""
        return self._config.get("vote_count_mode", 0)

    @vote_count_mode.setter
    def vote_count_mode(self, mode: int) -> None:
        self._config["vote_count_mode"] = mode
        self.update()

    @property
    async def democracy(self) -> list[discord.Member] | list:
        """Get democracy-privileged users"""
        try:
            ids: list[int] = self._config["democracy"]
            democracy_members = []
            for id_ in ids:
                member = self.guild.get_member(id_)
                if member is None:
                    democracy_members.append(await self.guild.fetch_member(id_))
                elif member is discord.Member:
                    democracy_members.append(member)
            return democracy_members
        except KeyError:
            return []

    @property
    def debug_tie(self) -> bool:
        return self._config.get("debug_tie", False)

    @debug_tie.setter
    def debug_tie(self, val: bool) -> None:
        self._config["debug_tie"] = val
        self.update()