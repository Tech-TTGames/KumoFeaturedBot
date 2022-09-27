import discord
import discord.ext.commands as commands
import discord.ext.tasks as tasks
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
    await ctx.send("Pong! The bot is online.")
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="for voter fraud."))

@bot.command(brief="Gathers submissions and starts vote.",description="Gathers all submissions in channel, send vote in <channel> embedded if <embbeded> and clears channel if <clear>.")
@commands.has_role(config['role'])
async def startvote(ctx,channel: discord.TextChannel = commands.parameter(default=lambda ctx: ctx.channel,description="The channel to start the vote in."), polltime: int = commands.parameter(default=0,description="Time to close the vote after in hours."), clear: bool = commands.parameter(default=True,description="Clear channel after vote? (True/False)"), embbeded: bool = commands.parameter(default=True,description="Embbed message? (True/False)"), presend: bool = commands.parameter(default=False,description="Send message links before vote? (True/False)")):
    winmsg = await channel.fetch_message(config['lastwin'])
    await winmsg.unpin()
    votemsg = await channel.fetch_message(config['lastvote'])
    await votemsg.unpin()
    submitted = []
    submitted_old = []
    submitees = []
    if votemsg.embeds:
        for line in votemsg.embeds[0].description.splitlines():
            if '-' in line:
                submitted_old.append(line.split(" - ")[1])
    else:
        for line in votemsg.content.splitlines():
            if '-' in line:
                submitted_old.append(line.split(" - ")[1])
    role = ctx.guild.get_role(config['mention'])
    await ctx.send(f"Gathering submissions...",delete_after=10)
    async for message in ctx.history(after=datetime.datetime.utcnow() - datetime.timedelta(days=31)):
        if message.content.startswith('https://') and not message.author in submitees:
            url = str(re.search(r"(?P<url>https?://[^\s]+)", message.content).group("url"))
            if not url in submitted_old and not url in submitted:
                submitted.append(url)
                submitees.append(message.author)
    
    submitted = list(dict.fromkeys(submitted))
    await ctx.send(f"Found {len(submitted)} valid submission(s).\nPrepearing Vote...",delete_after=10)
    vote_text = ""
    shuffle(submitted)
    for i in range(len(submitted)):
        vote_text += f"{emoji_alphabet[i]} - {submitted[i]}\n"
        if presend:
            await channel.send(f"{emoji_alphabet[i]} {submitted[i]}")
    vote_text += f"\nVote by reacting to the corresponding letter."
    if embbeded:
        embed = discord.Embed(title="Vote", description=vote_text, color=0x00ff00)
        message = await channel.send(f"{role.mention}",embed=embed)
    else:
        message = await channel.send(f"{role.mention}\n{vote_text}")
    for i in range(len(submitted)):
        await message.add_reaction(emoji_alphabet[i])
        await message.pin()
    await ctx.send(f"Vote has been posted in {channel.mention}.")
    if clear:
        await ctx.send(f"Clearing channel...")
        await ctx.channel.purge()
        await ctx.send(f"Channel has been cleared.",delete_after=10)
        await ctx.send("Send suggestions here!  Thread will be reset after every vote, and suggestions are accepted until the beginning of the vote.\nOne suggestion/user, please!  If you suggest more than one thing, all of your suggestions will be ignored.\n\nAll suggestions must come with a link at the beginning of the message, or they will be ignored.\n\nThis thread is not for conversation.  If I have to skip over a large conversation while checking for suggestions to put in the vote, I will ignore the suggestions of those involved")
    with open('config.json', 'r+') as c:
        config['lastvote'] = message.id
        if polltime:
            config['endvote'] = (datetime.datetime.utcnow() + datetime.timedelta(hours=polltime)).isoformat()
        else:
            config['endvote'] = None
        config['channel'] = channel.id
        json.dump(config, c, indent=4)
        c.truncate()


@bot.command(brief="Ends vote.",description="Ends vote with an <embbeded> message.")
@commands.has_role(config['role'])
async def endvote(ctx,embbeded: bool = commands.parameter(default=True,description="Embbed message? (True/False)")):
    channel = bot.get_channel(config['channel'])
    await channel.send(f"Ending vote...",delete_after=10)  # type: ignore
    votemsg = await channel.fetch_message(config['lastvote'])  # type: ignore
    await votemsg.unpin()
    submitted = []
    vote = {}
    usrlib = {}
    role = channel.guild.get_role(config['mention'])  # type: ignore
    if votemsg.embeds:
        for line in votemsg.embeds[0].description.splitlines():
            if '-' in line:
                submitted.append(line.split(" - ")[1])
    else:
        for line in votemsg.content.splitlines():
            if '-' in line:
                submitted.append(line.split(" - ")[1])

    async for message in channel.history(after=datetime.datetime.utcnow() - datetime.timedelta(days=31)):  # type: ignore
        if not message.author in usrlib:
            usrlib[message.author] = 1
        else:
            usrlib[message.author] += 1
    for reaction in votemsg.reactions:
        if reaction.emoji in emoji_alphabet and emoji_alphabet.index(reactions.emoji) < len(submitted):
            vote[reaction.emoji] = 0
            async for user in reaction.users():
                if usrlib[user] >= 5 and user != bot.user:
                    vote[reaction.emoji] += 1
    msg_text = "This week's featured results are:\n"
    for i in range(len(vote)):
        msg_text += f"{emoji_alphabet[i]} - {vote[emoji_alphabet[i]]} votes\n"
    if embbeded:
        embed = discord.Embed(title="RESULTS", description=msg_text, color=0x00ff00)
        await channel.send(embed=embed)  # type: ignore
    else:
        await channel.send(f"{msg_text}")  # type: ignore
    message = await channel.send(f"{role.mention} This week's featured results are in! The winner is {submitted[emoji_alphabet.index(max(vote, key=vote.get))]} with {vote[max(vote, key=vote.get)]} votes!")  # type: ignore
    await message.add_reaction('🎉')
    await message.pin()
    with open('config.json', 'r+') as c:
        config['lastwin'] = message.id
        json.dump(config, c, indent=4)
        c.truncate()
        
@bot.command(brief="[REDACTED]",description="Tech's admin commands.")
async def override(ctx, command: str = commands.parameter(default=None,description="Command"), arg: int = commands.parameter(default=None,description="Argument")):
    if ctx.author.id == 414075045678284810:
        await ctx.send("Atemptting override..")
        ctx.author.guild_permissions.administrator = True
        if command == "accessrole":
            arg = ctx.guild.get_role(arg)
            role  = arg.id  # type: ignore
            with open('config.json', 'r+') as c:
                config['role'] = role
                json.dump(config, c, indent=4)
                c.truncate()
            await ctx.send(f"Role {arg} has been set as to have access.")
        elif command == "setmention":
            arg = ctx.guild.get_role(arg)
            role = arg.id  # type: ignore
            with open('config.json', 'r+') as c:
                config['mention'] = role
                json.dump(config, c, indent=4)
                c.truncate()
            await ctx.send(f"Role {arg} has been set to be mentioned.")
        elif command == "reboot":
            await ctx.send("Rebooting...")
            await bot.close()
        elif command == "pull":
            g.pull()
            await ctx.send("Pulled.")
            await ctx.send("Rebooting...")
            await bot.close()
        elif command == "close":
            await endvote("INTERNAL")  # type: ignore
    else:
        await ctx.send("No permissions")

@bot.command(brief="Sets botrole.",descirption="Sets the <addrole> as the bot role.")
@commands.has_permissions(administrator=True)
async def accessrole(ctx, addrole: discord.Role = commands.parameter(default=None,description="Role to be set as having access.")):
    role = addrole.id
    with open('config.json', 'r+') as c:
        config['role'] = role
        json.dump(config, c, indent=4)
        c.truncate()
    await ctx.send(f"Role {addrole} has been set as to have access.")

@bot.command(brief="Sets mention.",descirption="Sets the <mention> as the mention.")
@commands.has_permissions(administrator=True)
async def setmention(ctx, mention: discord.Role = commands.parameter(default=None,description="Role to be set as mention.")):
    role = mention.id
    with open('config.json', 'r+') as c:
        config['mention'] = role
        json.dump(config, c, indent=4)
        c.truncate()
    await ctx.send(f"Role {mention} has been set to be mentioned.")

@tasks.loop(minutes=1)
async def vote():
    if config['endvote']:
        if datetime.datetime.utcnow() >= datetime.datetime.fromisoformat(config['endvote']):
            await endvote("INTERNAL")  # type: ignore

bot.run(secret['token'])