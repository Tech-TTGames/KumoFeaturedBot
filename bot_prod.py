"""This is the main file for the bot.
It contains a full version of the bot's commands and events.
"""
import logging
import datetime
import re
import os
from random import shuffle
import asyncio
import discord
from discord.ext import commands
from variables import intents, handler, EMOJI_ALPHABET, VERSION, Config, Secret

bot = commands.Bot(command_prefix='>', intents=intents)
config = Config(bot)
secret = Secret()
bot.command_prefix = config.prefix

def vote_running():
    '''Returns wether a vote is running.'''
    async def predicate(ctx):
        if not config.vote_running or ctx.author == bot.user:
            raise commands.CommandError("No vote is currently running.")
        return True
    return commands.check(predicate)

@bot.event
async def on_command_error(ctx, error):
    """The event triggered when an error is raised while invoking a command."""
    if hasattr(ctx.command, 'on_error'):
        return

    ignored = (commands.CommandNotFound, )
    error = getattr(error, 'original', error)

    if isinstance(error, ignored):
        return

    if isinstance(error, commands.DisabledCommand):
        await ctx.send(f'{ctx.command} has been disabled.')

    elif isinstance(error, commands.NoPrivateMessage):
        try:
            await ctx.author.send(f'{ctx.command} can not be used in Private Messages.')
        except discord.HTTPException:
            pass

    elif isinstance(error,commands.NotOwner):
        await ctx.send(f"{ctx.author.name} is not in the sudoers file."
        " This incident will be reported.")
        logging.warning("Unauthorized override attempt: %s", ctx.author.id)

    elif isinstance(error,(commands.CheckFailure,commands.CheckAnyFailure)):
        await ctx.send("You are missing permissions to run this command.")

    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"Missing required argument(s): {error.args}")

    elif isinstance(error,commands.BotMissingPermissions):
        await ctx.send("I'm missing permissions to execute the command!\n"
        f"{error.missing_permissions}")

    else:
        logging.exception('Ignoring exception %s in command %s:',
                            str(error),ctx.command,exc_info=error)

@bot.event
async def on_ready():
    """This event is called when the bot is ready to be used."""
    logging.info("%s has connected to Discord!", str(bot.user))
    if config.closetime:
        logging.info("Resuming vote at %s", config.closetime)
        await discord.utils.sleep_until(config.closetime)
        logging.info("Closing vote via INTERNAL event.")
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
    await ctx.send("KumoFeaturedBot " + VERSION +  " by Tech. TTGames#8616 is running.")

@bot.command(brief="Gathers submissions and starts vote.",
            description="""Gathers all submissions in channel.
Then sends vote in <channel> and clears channel if <clear>.""")
@commands.guild_only()
@commands.check_any(commands.has_role(config.role_id),commands.is_owner())
async def startvote(ctx,
                    cha: discord.TextChannel = commands.parameter(default=lambda ctx: ctx.channel,
                    description="The channel to start the vote in."),
                    polltime: int = commands.parameter(default=0,
                    description="Time to close the vote after in hours."),
                    clear: bool = commands.parameter(default=False,
                    description="Clear channel after vote? (True/False)"),
                    presend: bool = commands.parameter(default=False,
                    description="Send message links before vote? (True/False)")):
    """This command is used to start a vote."""
    winmsg = await config.lastwin
    if winmsg is not None:
        await winmsg.unpin()
    votemsg = await config.lastvote
    if votemsg is not None:
        await votemsg.unpin()
    submitted = []
    submitted_old = []
    submitees = []
    if votemsg is not None:
        if votemsg.embeds and votemsg.embeds[0].description and votemsg.embeds[0].title == "Vote":
            for line in votemsg.embeds[0].description.splitlines():
                if ' - ' in line:
                    submitted.append(line.split(" - ")[1].lstrip("<" ).rstrip(">"))
        else:
            for line in votemsg.content.splitlines():
                if ' - ' in line:
                    submitted.append(line.split(" - ")[1].lstrip("<").rstrip(">"))
    role = config.mention
    await ctx.send("Gathering submissions...",delete_after=10)
    async with ctx.typing():
        timed = discord.utils.utcnow() - datetime.timedelta(days=31)
        async for message in ctx.history(after=timed,limit=None):
            if message.content.startswith('https://') and not message.author in submitees:
                url = re.search(r"(?P<url>https?://[^\s]+)", message.content)
                if url not in submitted and url is not None and url not in submitted_old:
                    submitted.append(str(url.group("url")))
                    submitees.append(message.author)
    logging.debug("Old: %s", str(submitted_old))
    logging.debug("New: %s", str(submitted))
    submitted = list(dict.fromkeys(submitted))
    await ctx.send(f"Found {len(submitted)} valid submission(s).\nPrepearing Vote...",
                delete_after=10)
    vote_text = ""
    shuffle(submitted)
    for i, sub in enumerate(submitted):
        vote_text += f"{EMOJI_ALPHABET[i]} - <{sub}>\n"
        if presend:
            await cha.send(f"{EMOJI_ALPHABET[i]} {sub}")
    vote_text += "\nVote by reacting to the corresponding letter."
    if polltime:
        timed = discord.utils.utcnow() + datetime.timedelta(hours=polltime)
        vote_text += f"\nVote will close <t:{str(round(timed.timestamp()))}:R>."
    embed = discord.Embed(title="Vote", description=vote_text, color=0x00ff00)
    message = await cha.send(f"{role.mention}",embed=embed)
    for i in range(len(submitted)):
        await message.add_reaction(EMOJI_ALPHABET[i])
    await message.pin()
    await ctx.send(f"Vote has been posted in {cha.mention}.")
    if clear:
        await ctx.send("Clearing channel...",delete_after=10)
        await ctx.channel.purge()
        await ctx.send("Channel has been cleared.",delete_after=10)
        await ctx.send("Send suggestions here!\n"
        "Suggestions are accepted until the beginning of the vote.\n"
        "One suggestion/user, please! "
        "If you suggest more than one thing, all of the following suggestions will be ignored.\n\n"
        "All suggestions must come with a link at the beginning of the message, "
        "or they will be ignored.\n\n"
        "This thread is not for conversation.")
    logging.info("Vote started in %s by %s at %s",
    str(cha), str(ctx.author), str(discord.utils.utcnow()))
    config.lastvote = message
    config.channel = cha
    config.vote_running = True
    if polltime:
        config.closetime = timed
        await discord.utils.sleep_until(timed)
        logging.info("Closing vote in %s due to polltime end.",str(cha))
        await endvote(ctx)


@bot.command(brief="Ends vote.",description="Ends vote with a embbeded message.")
@commands.guild_only()
@commands.check_any(commands.has_role(config.role_id),commands.is_owner())
@vote_running()
async def endvote(ctx):
    """This command is used to end a vote."""
    channel = config.channel
    if ctx != 'INTERNAL':
        oper = ctx.author
    else:
        oper = 'system'
    await channel.send("Ending vote...", delete_after=10)
    votemsg = await config.lastvote
    if votemsg is None:
        raise commands.errors.CommandError("Vote message not found.")
    await votemsg.unpin()
    submitted = []
    vote = {}
    usrlib = {}
    role = config.mention
    await channel.send("Gathering votes and applying fraud protection... (This may take a while)")
    async with channel.typing():
        if votemsg.embeds and votemsg.embeds[0].description and votemsg.embeds[0].title == "Vote":
            for line in votemsg.embeds[0].description.splitlines():
                if ' - ' in line:
                    submitted.append(line.split(" - ")[1].lstrip("<" ).rstrip(">"))
        else:
            for line in votemsg.content.splitlines():
                if ' - ' in line:
                    submitted.append(line.split(" - ")[1].lstrip("<").rstrip(">"))
        timed = discord.utils.utcnow() - datetime.timedelta(days=31)
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
        msg_text += f"{EMOJI_ALPHABET[i]} - {vote[EMOJI_ALPHABET[i]]} vote" + \
        f"{'s'[:vote[EMOJI_ALPHABET[i]]^1]}\n"
    embed = discord.Embed(title="RESULTS", description=msg_text, color=0x00ff00)
    await channel.send(embed=embed)
    win_id = max(vote, key= vote.get)  # type: ignore
    message = await channel.send(f"{role.mention} This week's featured results are in!"
    f"The winner is {submitted[EMOJI_ALPHABET.index(win_id)]}"
    f" with {vote[win_id]} vote{'s'[:vote[win_id]^1]}!")
    await message.add_reaction('🎉')
    await message.pin()
    logging.info("Vote ended in %s by %s at %s",
    str(channel), str(oper), str(discord.utils.utcnow()))
    config.lastwin = message
    config.vote_running = False
    config.closetime = None

@bot.command(brief="Configure autoclose time.",description="Sets the autoclose time.")
@commands.check_any(commands.has_role(config.role_id),commands.is_owner())
@vote_running()
async def autoclose(ctx,
                time: int = commands.parameter(default=24,
                description="Time in hours.")):
    """This command is used to configure the autoclose time."""
    timed = discord.utils.utcnow() + datetime.timedelta(hours=time)
    config.closetime = timed
    await ctx.send(f"Vote will close <t:{str(round(config.closetime_timestamp))}:R>.")
    await discord.utils.sleep_until(timed)
    await endvote(ctx)

@bot.command(brief="[REDACTED]",description="Tech's admin commands.")
@commands.is_owner()
async def override(ctx,
                command: str = commands.parameter(default=None,description="Command")):
    """This command is used to override the bot's commands."""
    await ctx.send("Atemptting override..")
    await ctx.send(f"Command: {command}")
    logging.info("Owner override triggered: %s", command)
    if command == "reboot":
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
            logging.info('[stdout]\n%s', stdo.decode())
        if stdr:
            await ctx.author.send(f'[stderr]\n{stdr.decode()}')
            logging.info('[stderr]\n%s', stdr.decode())
        await ctx.send("Rebooting...")
        logging.info("Rebooting...")
        await bot.close()
    elif command == "debug":
        config.mode = "debug"
        logging.info("Rebooting with debug mode...")
        await ctx.send("Debug mode enabling...")
        await bot.close()
    else:
        await ctx.send("Invalid override command.")

@bot.command(brief="Sets botrole.",descirption="Sets the <addrole> as the bot role.")
@commands.check_any(commands.has_permissions(administrator=True),commands.is_owner())
async def accessrole(ctx,
                    addrole: discord.Role = commands.parameter(default=None,
                    description="Role to be set as having access.")):
    """Sets the <addrole> as the bot role."""
    config.role = addrole
    await ctx.send(f"Role {addrole} has been set as to have access.")

@bot.command(brief="Sets mention.",descirption="Sets the <mention> as the mention.")
@commands.check_any(commands.has_permissions(administrator=True),commands.is_owner())
async def setmention(ctx,
                    mention: discord.Role = commands.parameter(default=None,
                    description="Role to be set as mention.")):
    """Sets the <mention> as the mention."""
    config.mention = mention
    await ctx.send(f"Role {mention} has been set to be mentioned.")

def start():
    """Starts the bot."""
    bot.run(secret.token, log_handler=handler, root_logger=True)

if __name__ == '__main__':
    start()
