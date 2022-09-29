"""This is the main file for the bot.
It contains a full version of the bot's commands and events.
"""
import logging
from logging.handlers import RotatingFileHandler
import json
import datetime
import re
import os
import asyncio
from random import shuffle
from typing import cast
import discord
from discord.ext import commands
from ver import current_version

with open('secret.json', encoding="utf-8") as f:
    secret = json.load(f)

intents = discord.Intents.default()
intents.message_content = True # pylint: disable=assigning-non-slot
intents.messages = True # pylint: disable=assigning-non-slot
bot = commands.Bot(command_prefix='>', intents=intents)
handler = RotatingFileHandler(filename='discord.log',
                            encoding='utf-8',
                            mode='w',
                            backupCount=10,
                            maxBytes=100000)
EMOJI_ALPHABET = ["\U0001F1E6","\U0001F1E7","\U0001F1E8","\U0001F1E9","\U0001F1EA","\U0001F1EB",
                "\U0001F1EC","\U0001F1ED","\U0001F1EE","\U0001F1EF","\U0001F1F0","\U0001F1F1",
                "\U0001F1F2","\U0001F1F3","\U0001F1F4","\U0001F1F5","\U0001F1F6","\U0001F1F7",
                "\U0001F1F8","\U0001F1F9","\U0001F1FA","\U0001F1FB","\U0001F1FC","\U0001F1FD",
                "\U0001F1FE","\U0001F1FF"]
with open('config.json', encoding="utf-8") as c:
    config = json.load(c)

@bot.event
async def on_ready():
    """This event is called when the bot is ready to be used."""
    logging.info("%i has connected to Discord!", bot.user)
    if config['closetime']:
        closetime = datetime.datetime.fromisoformat(config['closetime'])
        logging.info("Resuming vote at %s", closetime)
        await asyncio.sleep(int((closetime - datetime.datetime.utcnow()).total_seconds()))
        await endvote("INTERNAL")  # type: ignore

@bot.command(brief="Pings the bot.",
            description="Pings the bot. What do you expect.")
async def ping(ctx):
    """This command is used to check if the bot is online."""
    await ctx.send("Pong! The bot is online.\nPing: " + str(round(bot.latency * 1000)) + "ms")
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching,
                            name="for voter fraud."))

@bot.command(brief="Displays the current version",
            description="Displays the current version of the bot.")
async def version(ctx):
    """This command is used to check the current version of the bot."""
    await ctx.send("Current version: " + current_version())

@bot.command(brief="Gathers submissions and starts vote.",
            description="""Gathers all submissions in channel.
Then sends vote in <channel> embedded if <embbeded> and clears channel if <clear>.""")
@commands.has_role(config['role'])
async def startvote(ctx,
                    cha: discord.TextChannel = commands.parameter(default=lambda ctx: ctx.channel,
                    description="The channel to start the vote in."),
                    polltime: int = commands.parameter(default=0,
                    description="Time to close the vote after in hours."),
                    clear: bool = commands.parameter(default=True,
                    description="Clear channel after vote? (True/False)"),
                    embbeded: bool = commands.parameter(default=True,
                    description="Embbed message? (True/False)"),
                    presend: bool = commands.parameter(default=False,
                    description="Send message links before vote? (True/False)")):
    """This command is used to start a vote."""
    winmsg = await cha.fetch_message(config['lastwin'])
    await winmsg.unpin()
    votemsg = await cha.fetch_message(config['lastvote'])
    await votemsg.unpin()
    submitted = []
    submitted_old = []
    submitees = []
    if votemsg.embeds:
        if votemsg.embeds[0].description:
            for line in votemsg.embeds[0].description.splitlines():
                if '-' in line:
                    submitted_old.append(line.split(" - ")[1])
    else:
        for line in votemsg.content.splitlines():
            if '-' in line:
                submitted_old.append(line.split(" - ")[1])
    role = ctx.guild.get_role(config['mention'])
    await ctx.send("Gathering submissions...",delete_after=10)
    async with ctx.typing():
        timed = datetime.datetime.utcnow() - datetime.timedelta(days=31)
        async for message in ctx.history(after=timed,limit=None):
            if message.content.startswith('https://') and not message.author in submitees:
                url = re.search(r"(?P<url>https?://[^\s]+)", message.content)
                if url not in submitted and url is not None:
                    submitted.append(str(url.group("url")))
                    submitees.append(message.author)
    logging.debug("Old: %o", str(submitted_old))
    logging.debug("New: %s", str(submitted))
    submitted = list(dict.fromkeys(submitted))
    await ctx.send(f"Found {len(submitted)} valid submission(s).\nPrepearing Vote...",
                delete_after=10)
    vote_text = ""
    shuffle(submitted)
    for i, sub in enumerate(submitted):
        vote_text += f"{EMOJI_ALPHABET[i]} - {sub}\n"
        if presend:
            await cha.send(f"{EMOJI_ALPHABET[i]} {sub}")
    vote_text += "\nVote by reacting to the corresponding letter."
    if embbeded:
        embed = discord.Embed(title="Vote", description=vote_text, color=0x00ff00)
        message = await cha.send(f"{role.mention}",embed=embed)
    else:
        message = await cha.send(f"{role.mention}\n{vote_text}")
    for i in range(len(submitted)):
        await message.add_reaction(EMOJI_ALPHABET[i])
        await message.pin()
    await ctx.send(f"Vote has been posted in {cha.mention}.")
    if clear:
        await ctx.send("Clearing channel...")
        await ctx.channel.purge()
        await ctx.send("Channel has been cleared.",delete_after=10)
        await ctx.send("Send suggestions here! "
        "Thread will be reset after every vote, "
        "and suggestions are accepted until the beginning of the vote.\n"
        "One suggestion/user, please! "
        "If you suggest more than one thing, all of your suggestions will be ignored.\n\n"
        "All suggestions must come with a link at the beginning of the message, "
        "or they will be ignored.\n\n"
        "This thread is not for conversation.")
    logging.info("Vote started in %x by %s at %c",
    str(cha), str(ctx.author), str(datetime.datetime.utcnow()))
    with open('config.json', 'r+',encoding="utf-8") as c_upstart:
        config['lastvote'] = message.id
        config['channel'] = cha.id
        json.dump(config, c_upstart, indent=4)
        c_upstart.truncate()
    if polltime:
        await cha.send(f"Vote will close in {polltime} hours.")
        await asyncio.sleep(polltime*3600)
        await endvote(ctx,embbeded)


@bot.command(brief="Ends vote.",description="Ends vote with an <embbeded> message.")
@commands.has_role(config['role'])
async def endvote(ctx,
                embbeded: bool = commands.parameter(default=True,
                description="Embbed message? (True/False)")):
    """This command is used to end a vote."""
    channel = bot.get_channel(config['channel'])
    if not(channel is discord.TextChannel or channel is discord.Thread):
        raise commands.errors.CommandError("No vote in progress.")
    if ctx:
        oper = ctx.author
    else:
        oper = 'system'
    channel = cast(discord.TextChannel, channel)
    await channel.send("Ending vote...", delete_after=10)
    votemsg = await channel.fetch_message(config['lastvote'])
    await votemsg.unpin()
    submitted = []
    vote = {}
    usrlib = {}
    role = channel.guild.get_role(config['mention'])
    role = cast(discord.Role, role)
    await channel.send("Gathering votes and applying fraud protection... (This may take a while)")
    async with channel.typing():
        if votemsg.embeds:
            if votemsg.embeds[0].description:
                for line in votemsg.embeds[0].description.splitlines():
                    if '-' in line:
                        submitted.append(line.split(" - ")[1])
        else:
            for line in votemsg.content.splitlines():
                if '-' in line:
                    submitted.append(line.split(" - ")[1])
        timed = datetime.datetime.utcnow() - datetime.timedelta(days=31)
        async for message in channel.history(after=timed,oldest_first=True,limit=None):
            if not message.author in usrlib:
                usrlib[message.author] = 1
            else:
                usrlib[message.author] += 1
        logging.debug("Submitted: %s", str(submitted))
        logging.debug("Users: %s", str(usrlib))
        for reaction in votemsg.reactions:
            if reaction.emoji in EMOJI_ALPHABET and \
                EMOJI_ALPHABET.index(reaction.emoji) < len(submitted):
                vote[reaction.emoji] = 0
                async for user in reaction.users():
                    if user != bot.user and user in usrlib:
                        if usrlib[user] >= 5:
                            vote[reaction.emoji] += 1
        logging.debug("Votes: %s", str(vote))
    msg_text = "This week's featured results are:\n"
    for i in range(len(vote)):
        msg_text += f"{EMOJI_ALPHABET[i]} - {vote[EMOJI_ALPHABET[i]]} votes\n"
    if embbeded:
        embed = discord.Embed(title="RESULTS", description=msg_text, color=0x00ff00)
        await channel.send(embed=embed)
    else:
        await channel.send(f"{msg_text}")
    message = await channel.send(f"{role.mention} This week's featured results are in!\n"
    f"The winner is {submitted[EMOJI_ALPHABET.index(max(vote, key=vote.get))]}" # type: ignore
    f" with {vote[max(vote, key=vote.get)]} votes!""")  # type: ignore
    await message.add_reaction('🎉')
    await message.pin()
    logging.info("Vote ended in %x by %s at %c",
    str(channel), str(oper), str(datetime.datetime.utcnow()))
    with open('config.json', 'r+', encoding="utf-8") as c_upend:
        config['lastwin'] = message.id
        config['closetime'] = None
        json.dump(config, c_upend, indent=4)
        c_upend.truncate()

@bot.command(brief="Configure autoclose time.",description="Sets the autoclose time.")
@commands.has_role(config['role'])
async def autoclose(ctx,
                time: int = commands.parameter(default=24,
                description="Time in hours.")):
    """This command is used to configure the autoclose time."""
    with open('config.json', 'r+', encoding="utf-8") as c_up:
        timed = datetime.datetime.utcnow() + datetime.timedelta(hours=time)
        config['closetime'] = timed.isoformat()
        json.dump(config, c_up, indent=4)
        c_up.truncate()
    await ctx.send(f"Vote close time set to {time} hours.")
    await asyncio.sleep(time*3600)
    await endvote(ctx)

@bot.command(brief="[REDACTED]",description="Tech's admin commands.")
async def override(ctx,
                command: str = commands.parameter(default=None,description="Command"),
                arg: int = commands.parameter(default=None,description="Argument")):
    """This command is used to override the bot's commands."""
    if ctx.author.id == 414075045678284810:
        await ctx.send("Atemptting override..")
        await ctx.send(f"Command: {command}")
        logging.info("Owner override triggered: %i", command)
        ctx.author.guild_permissions.administrator = True
        if command == "accessrole":
            role = ctx.guild.get_role(arg)
            await accessrole(ctx, role)
        elif command == "setmention":
            role = ctx.guild.get_role(arg)
            await setmention(ctx, role)
        elif command == "close":
            await endvote(ctx)
        elif command == "autoclose":
            await autoclose(ctx, arg)
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
        elif command == "debug":
            with open('config.json', 'r+', encoding="utf-8") as c_over_debug:
                config['mode'] = "debug"
                json.dump(config, c_over_debug, indent=4)
                c_over_debug.truncate()
            logging.info("Rebooting with production mode...")
            await ctx.send("Debug mode enabling...")
            await bot.close()
    else:
        await ctx.send("No permissions")
        await ctx.message.delete()
        logging.warning("Unauthorized override attempt: %i", ctx.author.id)

@bot.command(brief="Sets botrole.",descirption="Sets the <addrole> as the bot role.")
@commands.has_permissions(administrator=True)
async def accessrole(ctx,
                    addrole: discord.Role = commands.parameter(default=None,
                    description="Role to be set as having access.")):
    """Sets the <addrole> as the bot role."""
    role = addrole.id
    with open('config.json', 'r+', encoding="utf-8") as c_access:
        config['role'] = role
        json.dump(config, c_access, indent=4)
        c_access.truncate()
    await ctx.send(f"Role {addrole} has been set as to have access.")

@bot.command(brief="Sets mention.",descirption="Sets the <mention> as the mention.")
@commands.has_permissions(administrator=True)
async def setmention(ctx,
                    mention: discord.Role = commands.parameter(default=None,
                    description="Role to be set as mention.")):
    """Sets the <mention> as the mention."""
    role = mention.id
    with open('config.json', 'r+', encoding="utf-8") as c_mention:
        config['mention'] = role
        json.dump(config, c_mention, indent=4)
        c_mention.truncate()
    await ctx.send(f"Role {mention} has been set to be mentioned.")

def start():
    """Starts the bot."""
    bot.run(secret['token'], log_handler=handler)

if __name__ == '__main__':
    start()
