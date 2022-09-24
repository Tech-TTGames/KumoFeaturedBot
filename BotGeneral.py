import discord
import discord.ext.commands as commands
import logging
import json
import datetime
import re
from random import shuffle

with open('secret.json') as f:
    secret = json.load(f)

intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
bot = commands.Bot(command_prefix='>', intents=intents)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
emoji_alphabet = ["\U0001F1E6","\U0001F1E7","\U0001F1E8","\U0001F1E9","\U0001F1EA","\U0001F1EB","\U0001F1EC","\U0001F1ED","\U0001F1EE","\U0001F1EF","\U0001F1F0","\U0001F1F1","\U0001F1F2","\U0001F1F3","\U0001F1F4","\U0001F1F5","\U0001F1F6","\U0001F1F7","\U0001F1F8","\U0001F1F9","\U0001F1FA","\U0001F1FB","\U0001F1FC","\U0001F1FD","\U0001F1FE","\U0001F1FF"]
with open('config.json') as c:
    config = json.load(c)

@bot.event
async def on_ready():
    print(f"{bot.user} has connected to Discord!")

@bot.command()
async def ping(ctx):
    await ctx.send("Pong! The bot is online.")
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="for voter fraud"))

@bot.command()
@commands.has_role(config['role'])
async def startvote(ctx,channel: discord.TextChannel, clear: bool=True, embbeded: bool=True):
    submitted = []
    submitees = []
    role = ctx.guild.get_role(config['mention'])
    await ctx.send(f"Gathering submissions...",delete_after=10)
    async for message in ctx.history(after=datetime.datetime.utcnow() - datetime.timedelta(days=31)):
        if message.content.startswith('https://') and not message.author in submitees:
            url = str(re.search(r"(?P<url>https?://[^\s]+)", message.content).group("url"))
            submitted.append(url)
            submitees.append(message.author)
    
    submitted = list(dict.fromkeys(submitted))
    await ctx.send(f"Found {len(submitted)} valid submission(s).\nPrepearing Vote...",delete_after=10)
    vote_text = ""
    shuffle(submitted)
    for i in range(len(submitted)):
        vote_text += f"{emoji_alphabet[i]} - {submitted[i]}\n"
    vote_text += f"\nVote by reacting to the corresponding letter."
    if embbeded:
        embed = discord.Embed(title="Vote", description=vote_text, color=0x00ff00)
        message = await channel.send(f"{role.mention}",embed=embed)
    else:
        message = await channel.send(f"{role.mention}\n{vote_text}")
    for i in range(len(submitted)):
        await message.add_reaction(emoji_alphabet[i])
    await ctx.send(f"Vote has been posted in {channel.mention}.")
    if clear:
        await ctx.send(f"Clearing channel...")
        await ctx.channel.purge()
        await ctx.send(f"Channel has been cleared.",delete_after=10)


@bot.command()
@commands.has_role(config['role'])
async def endvote(ctx, votemsg: discord.Message, embbeded: bool=True):
    await ctx.send(f"Ending vote...",delete_after=10)
    submitted = []
    vote = {}
    usrlib = {}
    role = ctx.guild.get_role(config['mention'])
    if votemsg.embeds:
        for line in votemsg.embeds[0].description.splitlines():
            if '-' in line:
                submitted.append(line.split(" - ")[1])
    else:
        for line in votemsg.content.splitlines():
            if '-' in line:
                submitted.append(line.split(" - ")[1])

    async for message in ctx.history(after=datetime.datetime.utcnow() - datetime.timedelta(days=31)):
        if not message.author in usrlib:
            usrlib[message.author] = 1
        else:
            usrlib[message.author] += 1
    for reaction in votemsg.reactions:
        if reaction.emoji in emoji_alphabet:
            vote[reaction.emoji] = 0
            async for user in reaction.users():
                if usrlib[user] >= 5:
                    vote[reaction.emoji] += 1
    msg_text = "This week's featured results are:\n"
    for i in range(len(vote)):
        msg_text += f"{emoji_alphabet[i]} - {vote[emoji_alphabet[i]]} votes\n"
    if embbeded:
        embed = discord.Embed(title="RESULTS", description=msg_text, color=0x00ff00)
        message = await ctx.send(embed=embed)
    else:
        message = await ctx.send(f"{msg_text}")
    await ctx.send(f"{role.mention} This week's featured results are in! The winner is {submitted[emoji_alphabet.index(max(vote, key=vote.get))]} with {vote[max(vote, key=vote.get)]} votes!")
    

@bot.command()
@commands.has_permissions(administrator=True)
async def accessrole(ctx, addrole: discord.Role):
    role = addrole.id
    with open('config.json', 'r+') as c:
        config['role'] = role
        json.dump(config, c, indent=4)
        c.truncate()
    await ctx.send(f"Role {addrole} has been set as to have access.")

@bot.command()
@commands.has_permissions(administrator=True)
async def setmention(ctx, mention: discord.Role):
    role = mention.id
    with open('config.json', 'r+') as c:
        config['mention'] = role
        json.dump(config, c, indent=4)
        c.truncate()
    await ctx.send(f"Role {mention} has been set to be mentioned.")


bot.run(secret['token'])