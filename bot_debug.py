"""This is the main file for the bot in debug mode.
It contains a limited version of the bot's commands and events.
"""
import logging
from logging.handlers import RotatingFileHandler
import json
import datetime
import re
import os
import asyncio
import discord
from discord.ext import commands
from bot_control import current_ver

with open('secret.json',encoding="utf-8") as f:
    secret = json.load(f)

intents = discord.Intents.default()
intents.message_content = True # pylint: disable=assigning-non-slot
intents.messages = True # pylint: disable=assigning-non-slot
bot = commands.Bot(command_prefix='>', intents=intents)
handler = RotatingFileHandler(filename='discord.log', encoding='utf-8', mode='w',backupCount=10,maxBytes=100000)
emoji_alphabet = ["\U0001F1E6","\U0001F1E7","\U0001F1E8","\U0001F1E9","\U0001F1EA","\U0001F1EB",
                "\U0001F1EC","\U0001F1ED","\U0001F1EE","\U0001F1EF","\U0001F1F0","\U0001F1F1",
                "\U0001F1F2","\U0001F1F3","\U0001F1F4","\U0001F1F5","\U0001F1F6","\U0001F1F7",
                "\U0001F1F8","\U0001F1F9","\U0001F1FA","\U0001F1FB","\U0001F1FC","\U0001F1FD",
                "\U0001F1FE","\U0001F1FF"]
with open('config.json',encoding="utf-8") as c:
    config = json.load(c)

@bot.event
async def on_ready():
    """This event is called when the bot is ready to be used."""
    logging.info("%i has connected to Discord!", bot.user)

@bot.command(brief="Pings the bot.",description="Pings the bot. What do you expect.")
async def ping(ctx):
    """This command is used to check if the bot is online."""
    await ctx.send("Pong! The bot is online.\nPing: " +
                str(round(bot.latency * 1000)) +
                "ms\nWarning! This bot is currently in debug mode.")
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.playing,
                                                        name="with fire. [DEBUG MODE]"))

@bot.command(brief="Displays the current version",description="Displays the current version of the bot.")
async def version(ctx):
    """This command is used to check the current version of the bot."""
    await ctx.send("Current version: " + current_ver())

@bot.command(brief="[REDACTED]",description="Tech's admin commands.")
async def override(ctx, command: str = commands.parameter(default=None,description="Command")):
    """Various commands for testing."""
    if ctx.author.id == 414075045678284810:
        await ctx.send("Atemptting override..")
        logging.info("Owner override triggered: %i", command)
        ctx.author.guild_permissions.administrator = True
        if command == "testhist":
            async with ctx.typing():
                usrlib = {}
                vote = {}
                channel = ctx.guild.get_channel(config['channel'])
                votemsg = await channel.fetch_message(config['lastvote'])
                timed = datetime.datetime.utcnow() - datetime.timedelta(days=31)
                async for message in channel.history(after=timed,limit=None):
                    if not message.author in usrlib:
                        usrlib[message.author] = 1
                    else:
                        usrlib[message.author] += 1
                for reaction in votemsg.reactions:
                    if reaction.emoji in emoji_alphabet:
                        vote[reaction.emoji] = 0
                        async for user in reaction.users():
                            if user != bot.user and user in usrlib:
                                if usrlib[user] >= 5:
                                    vote[reaction.emoji] += 1
                await ctx.author.send(vote)
                logging.debug("Test History results %a", vote)
        elif command == "testget":
            submitted = []
            submitees = []
            await ctx.send("Gathering submissions...",delete_after=10)
            async with ctx.typing():
                timed = datetime.datetime.utcnow() - datetime.timedelta(days=31)
                async for message in ctx.history(after=timed,limit=None):
                    if message.content.startswith('https://') and not message.author in submitees:
                        url = re.search(r"(?P<url>https?://[^\s]+)", message.content)
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
            pull = await asyncio.create_subprocess_shell("git pull",
                                                        stdout=asyncio.subprocess.PIPE,
                                                        stderr=asyncio.subprocess.PIPE,
                                                        cwd=os.getcwd())
            stdo, stdr = await pull.communicate()
            await ctx.send("Pulled.")
            if stdo:
                await ctx.author.send(f'[stdout]\n{stdo.decode()}')
                logging.info('[stdout]\n%i', stdo.decode())
            if stdr:
                await ctx.author.send(f'[stderr]\n{stdr.decode()}')
                logging.info('[stderr]\n%i', stdr.decode())
            await ctx.send("Rebooting...")
            logging.info("Rebooting...")
            await bot.close()
        elif command == "prod":
            with open('config.json', 'r+',encoding="utf-8") as c_over_prod:
                config['mode'] = "prod"
                json.dump(config, c_over_prod, indent=4)
                c_over_prod.truncate()
            logging.info("Rebooting with production mode...")
            await ctx.send("Switching to normal mode...")
            await bot.close()
    else:
        await ctx.send("No permissions")
        await ctx.message.delete()
        logging.warning("Unauthorized override attempt: %i", ctx.author.id)

def start():
    """Starts the bot."""
    bot.run(secret['token'], log_handler=handler, log_level=logging.DEBUG)

if __name__ == '__main__':
    start()
