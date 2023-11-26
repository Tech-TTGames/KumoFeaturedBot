"""This is the main file for the bot in debug mode.
It contains a limited version of the bot's commands and events.
"""
import asyncio
import datetime
import logging
import os
import re

import discord
from discord.ext import commands

from variables import EMOJI_ALPHABET, VERSION, Config, Secret, handler, intents

bot = commands.Bot(command_prefix="<", intents=intents)
config = Config(bot)
secret = Secret()


@bot.event
async def on_ready():
    """This event is called when the bot is ready to be used."""
    logging.info("%s has connected to Discord!", str(bot.user))


@bot.command(brief="Pings the bot.", description="Pings the bot. What do you expect.")
async def ping(ctx):
    """This command is used to check if the bot is online."""
    await ctx.send(
        "Pong! The bot is online.\nPing: "
        + str(round(bot.latency * 1000))
        + "ms\n*Warning! This bot is currently in debug mode.*"
    )
    await bot.change_presence(
        status=discord.Status.dnd,
        activity=discord.Activity(
            type=discord.ActivityType.playing, name="with fire. [DEBUG MODE]"
        ),
    )


@bot.command(
    brief="Displays the current version",
    description="Displays the current version of the bot.",
)
async def version(ctx):
    """This command is used to check the current version of the bot."""
    await ctx.send(
        "KumoFeaturedBot " + VERSION + " by Tech. TTGames#8616 is running."
        "\n*Warning! This bot is currently in debug mode.*"
    )


@bot.command(brief="[REDACTED]", description="Tech's admin commands.")
@commands.is_owner()
async def override(
    ctx, command: str = commands.parameter(default=None, description="Command")
):
    """Various commands for testing."""
    await ctx.send("Attempting override..")
    logging.info("Owner override triggered: %s", command)

    if command == "testhist":
        async with ctx.typing():
            usrlib = {}
            vote = {}
            channel = config.channel
            votemsg = await config.lastvote
            timed = discord.utils.utcnow() - datetime.timedelta(days=31)
            async for message in channel.history(after=timed, limit=None):
                if message.author not in usrlib:
                    usrlib[message.author] = 1
                else:
                    usrlib[message.author] += 1
            if votemsg:
                for reaction in votemsg.reactions:
                    if reaction.emoji in EMOJI_ALPHABET:
                        vote[reaction.emoji] = 0
                        async for user in reaction.users():
                            if user != bot.user and user in usrlib:
                                # Splitting up the if statement to avoid KeyError
                                if usrlib[user] >= 5:
                                    vote[reaction.emoji] += 1
            else:
                vote = "No vote message found."
            await ctx.author.send(vote)
            logging.debug("Test History results %s", vote)

    elif command == "testget":
        submitted = []
        submitees = []
        await ctx.send("Gathering submissions...", delete_after=10)
        async with ctx.typing():
            timed = discord.utils.utcnow() - datetime.timedelta(days=31)
            async for message in ctx.history(after=timed, limit=None):
                if (
                    message.content.startswith("https://")
                    and message.author not in submitees
                ):
                    url = re.search(r"(?P<url>https?://\S+)", message.content)
                    if url not in submitted and url is not None:
                        submitted.append(str(url.group("url")))
                        submitees.append(message.author)
        submitted = list(dict.fromkeys(submitted))
        await ctx.author.send(submitted)
        logging.debug("Test Gathering results %s", submitted)

    elif command == "reboot":
        logging.info("Rebooting...")
        await ctx.send("Rebooting...")
        await bot.close()

    elif command == "pull":
        pull = await asyncio.create_subprocess_shell(
            "git pull",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=os.getcwd(),
        )
        stdo, stdr = await pull.communicate()
        await ctx.send("Pulled.")
        if stdo:
            await ctx.author.send(f"[stdout]\n{stdo.decode()}")
            logging.info("[stdout]\n%s", stdo.decode())
        if stdr:
            await ctx.author.send(f"[stderr]\n{stdr.decode()}")
            logging.info("[stderr]\n%s", stdr.decode())
        await ctx.send("Rebooting...")
        logging.info("Rebooting...")
        await bot.close()

    elif command == "prod":
        config.mode = "prod"
        logging.info("Rebooting with production mode...")
        await ctx.send("Switching to normal mode...")
        await bot.close()

    else:
        await ctx.send("Invalid override command.")


@bot.command(brief="Config editor", description="Tech's config editor.")
@commands.is_owner()
async def edit_config(
    ctx,
    setting: str = commands.parameter(default=None, description="Setting to adjust"),
    value: int = commands.parameter(default=None, description="Value to set to"),
):
    """Edits server-side config.json file."""
    if setting == "guild":
        gld = ctx.guild
        config.guild = gld
        await ctx.send(f"Guild set to {gld}")

    elif setting == "channel":
        chn = ctx.channel
        config.channel = chn
        await ctx.send(f"Channel set to {chn.mention}")

    elif setting == "lastvote":
        if value is None:
            raise commands.BadArgument("Missing message ID")
        config.lastvote = await config.channel.fetch_message(value)
        await ctx.send(f"Last vote set to {value}")

    elif setting == "lastwin":
        if value is None:
            raise commands.BadArgument("Missing message ID")
        config.lastwin = await config.channel.fetch_message(value)
        await ctx.send(f"Last win set to {value}")

    elif setting == "voterunning":
        if value is None:
            raise commands.BadArgument("Missing status.")
        config.vote_running = bool(value)
        await ctx.send(f"Vote running set to {bool(value)}")


def start():
    """Starts the bot."""
    bot.run(
        secret.token, log_handler=handler, log_level=logging.DEBUG, root_logger=True
    )


if __name__ == "__main__":
    start()
