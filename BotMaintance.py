import discord
import discord.ext.commands as commands
import logging
import json
import datetime
import re
import git
import pathlib
from random import shuffle

with open('secret.json') as f:
    secret = json.load(f)

intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
g = git.cmd.Git(pathlib.Path(__file__).parent.resolve())
bot = commands.Bot(command_prefix='>', intents=intents)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
emoji_alphabet = ["\U0001F1E6","\U0001F1E7","\U0001F1E8","\U0001F1E9","\U0001F1EA","\U0001F1EB","\U0001F1EC","\U0001F1ED","\U0001F1EE","\U0001F1EF","\U0001F1F0","\U0001F1F1","\U0001F1F2","\U0001F1F3","\U0001F1F4","\U0001F1F5","\U0001F1F6","\U0001F1F7","\U0001F1F8","\U0001F1F9","\U0001F1FA","\U0001F1FB","\U0001F1FC","\U0001F1FD","\U0001F1FE","\U0001F1FF"]
with open('config.json') as c:
    config = json.load(c)

@bot.event
async def on_ready():
    print(f"{bot.user} has connected to Discord!")

@bot.command(brief="Pings the bot.",description="Pings the bot. What do you expect.")
async def ping(ctx):
    await ctx.send("Pong! The bot is online.\nPing: " + str(round(bot.latency * 1000)) + "ms\nWarning! This bot is currently in debug mode.")
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.playing, name="with fire. [DEBUG MODE]"))
        
@bot.command(brief="[REDACTED]",description="Tech's admin commands.")
async def override(ctx, command: str = commands.parameter(default=None,description="Command"), arg: int = commands.parameter(default=None,description="Argument")):
    if ctx.author.id == 414075045678284810:
        await ctx.send("Atemptting override..")
        ctx.author.guild_permissions.administrator = True
        if command == "testhist":
            async with ctx.typing():
                usrlib = {}
                vote = {}
                channel = ctx.guild.get_channel(config['channel'])
                votemsg = await channel.fetch_message(config['lastvote'])
                async for message in channel.history(after=datetime.datetime.utcnow() - datetime.timedelta(days=31),oldest_first=True,limit=None):
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
        elif command == "testget":
                submitted = []
                submitees = []
                await ctx.send(f"Gathering submissions...",delete_after=10)
                async with ctx.typing():
                    async for message in ctx.history(after=datetime.datetime.utcnow() - datetime.timedelta(days=31),limit=None):
                        if message.content.startswith('https://') and not message.author in submitees:
                            url = str(re.search(r"(?P<url>https?://[^\s]+)", message.content).group("url"))
                            if not url in submitted:
                                submitted.append(url)
                                submitees.append(message.author)
                submitted = list(dict.fromkeys(submitted))
                await ctx.author.send(submitted)
        elif command == "reboot":
            await ctx.send("Rebooting...")
            await bot.close()
        elif command == "pull":
            g.pull()
            await ctx.send("Pulled.")
            await ctx.send("Rebooting...")
            await bot.close()
        elif command == "prod":
            with open('config.json', 'r+') as c:
                config['mode'] = "prod"
                json.dump(config, c, indent=4)
                c.truncate()
            await ctx.send("Debug mode enabling...")
            await bot.close()
    else:
        await ctx.send("No permissions")

bot.run(secret['token'], log_handler=handler, log_level=logging.DEBUG)