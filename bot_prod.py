"""This is the main file for the bot.
It contains a full version of the bot's commands and events.
"""
import asyncio
import datetime
import logging
import os
import re
from copy import deepcopy
from random import choice, shuffle
from typing import Dict, List, Union

import discord
from discord import app_commands
from discord.ext import commands

from variables import EMOJI_ALPHABET, VERSION, Config, Secret, handler, intents

bot = commands.Bot(
    command_prefix=">",
    intents=intents,
    status=discord.Status.online,
    activity=discord.Activity(
        type=discord.ActivityType.watching, name="for voter fraud."
    ),
)
config = Config(bot)
secret = Secret()
bot.command_prefix = config.prefix


def vote_running():
    """Returns wether a vote is running."""

    async def predicate(ctx: discord.Interaction):
        """The predicate for the check."""
        if not config.vote_running or ctx.user == bot.user:
            raise app_commands.CheckFailure("No vote is currently running.")
        return True

    return app_commands.check(predicate)


def is_owner():
    """Returns wether the user is the owner of the bot."""

    async def predicate(ctx: discord.Interaction):
        """The predicate for the check."""
        if ctx.user.id != 414075045678284810:
            raise app_commands.CheckFailure("You are not the owner of this bot.")
        return True

    return app_commands.check(predicate)


@bot.event
async def on_command_error(ctx: discord.Interaction, error):
    """The event triggered when an error is raised while invoking a command."""
    if hasattr(ctx.command, "on_error"):
        return

    ignored = (app_commands.CommandNotFound,)
    error = getattr(error, "original", error)

    if isinstance(error, ignored):
        return

    if isinstance(error, app_commands.NoPrivateMessage):
        try:
            await ctx.user.send(f"{ctx.command} can not be used in Private Messages.")
        except discord.HTTPException:
            pass

    elif isinstance(error, (app_commands.CheckFailure)):
        await ctx.response.send_message(error, ephemeral=True)

    elif isinstance(error, app_commands.BotMissingPermissions):
        await ctx.response.send_message(
            "I'm missing permissions to execute the command!\n"
            f"{error.missing_permissions}",
            ephemeral=True,
        )

    elif isinstance(error, app_commands.MissingRole):
        await ctx.response.send_message(
            "You are missing the role to run this command.", ephemeral=True
        )

    else:
        logging.exception(
            "Ignoring exception %s in command %s:",
            str(error),
            ctx.command,
            exc_info=error,
        )


@bot.event
async def on_ready():
    """This event is called when the bot is ready to be used."""
    logging.info("%s has connected to Discord!", str(bot.user))
    if config.armed:
        return
    if config.closetime:
        config.armed = True
        logging.info("Resuming vote at %s", config.closetime)
        await discord.utils.sleep_until(config.closetime)
        if not config.vote_running:
            logging.info("Vote already closed.")
            return
        logging.info("Closing vote via INTERNAL event.")
        await endvote_internal("INTERNAL")  # type: ignore
    config.armed = True


@bot.tree.command(name="ping", description="Pings the bot.")
async def ping(interaction: discord.Interaction) -> None:
    """This command is used to check if the bot is online."""
    await interaction.response.send_message(
        "Pong! The bot is online.\nPing: " + str(round(bot.latency * 1000)) + "ms"
    )


@bot.tree.command(
    name="version", description="Displays the current version of the bot."
)
async def version(interaction: discord.Interaction) -> None:
    """This command is used to check the current version of the bot."""
    await interaction.response.send_message(
        "KumoFeaturedBot " + VERSION + " by Tech. TTGames#8616 is running."
    )


@bot.tree.command(name="startvote", description="Starts a vote.")
@app_commands.guild_only()
@app_commands.checks.has_any_role(config.role_id, config.owner_role)
@app_commands.describe(
    cha="The channel to start the vote in.",
    polltime="Time to close the vote after in hours.",
    clear="Clear channel after vote? (True/False)",
    presend="Send message links before vote? (True/False)",
    cap="Max submissions to vote on.",
)
@app_commands.rename(cha="channel")
async def startvote(
    interaction: discord.Interaction,
    cha: discord.TextChannel,
    polltime: int = 0,
    clear: bool = False,
    presend: bool = False,
    cap: int = 8,
) -> None:
    """This command is used to start a vote."""
    submitted = []
    submitted_old = []
    submitees = []

    intchannel = interaction.channel
    if (
        isinstance(
            intchannel,
            (discord.StageChannel, discord.ForumChannel, discord.CategoryChannel),
        )
        or intchannel is None
    ):
        raise app_commands.AppCommandError("This channel is not a text channel.")

    winmsg = await config.lastwin
    if winmsg is not None:
        await winmsg.unpin()

    votemsg = await config.lastvote
    if votemsg is not None:
        await votemsg.unpin()

    if votemsg is not None:
        if (
            votemsg.embeds
            and votemsg.embeds[0].description
            and votemsg.embeds[0].title == "Vote"
        ):
            for line in votemsg.embeds[0].description.splitlines():
                if " - " in line:
                    submitted_old.append(line.split(" - ")[1].lstrip("<").rstrip(">"))
        else:
            for line in votemsg.content.splitlines():
                if " - " in line:
                    submitted_old.append(line.split(" - ")[1].lstrip("<").rstrip(">"))

    role = config.mention
    await interaction.response.defer(thinking=True)
    async with intchannel.typing():
        timed = discord.utils.utcnow() - datetime.timedelta(days=31)
        async for message in intchannel.history(after=timed, limit=None):
            if (
                message.content.startswith("https://")
                and message.author not in submitees
            ):
                url = re.search(r"(?P<url>https?://[^\s]+)", message.content)
                if (
                    url not in submitted
                    and url is not None
                    and url not in submitted_old
                ):
                    submitted.append(str(url.group("url")))
                    submitees.append(message.author)
    logging.debug("Old: %s", str(submitted_old))
    logging.debug("New: %s", str(submitted))
    submitted = list(dict.fromkeys(submitted))  # Remove duplicates
    shuffle(submitted)

    await intchannel.send(
        f"Found {len(submitted)} valid submission(s).\nPreparing Vote...",
        delete_after=60,
    )

    if len(submitted) > cap:
        await intchannel.send(
            f"Vote capped at {cap} submissions."
            f" {len(submitted)-cap} submissions dismissed.",
            delete_after=60,
        )
        submitted = submitted[:cap]

    vote_text = ""
    for i, sub in enumerate(submitted):
        vote_text += f"{EMOJI_ALPHABET[i]} - <{sub}>\n"
        if presend:
            await cha.send(f"{EMOJI_ALPHABET[i]} {sub}")

    vote_text += "\nVote by reacting to the corresponding letter."
    if polltime:
        timed = discord.utils.utcnow() + datetime.timedelta(hours=polltime)
        vote_text += f"\nVote will close <t:{str(round(timed.timestamp()))}:R>."
    embed = discord.Embed(title="Vote", description=vote_text, color=0x00FF00)

    message = await cha.send(f"{role.mention}", embed=embed)
    for i in range(len(submitted)):
        await message.add_reaction(EMOJI_ALPHABET[i])

    await message.pin()
    await interaction.followup.send(f"Vote has been posted in {cha.mention}.")

    if clear:
        await intchannel.send("Clearing channel...", delete_after=60)
        try:
            await intchannel.purge(bulk=True)  # type: ignore
        except discord.Forbidden:
            await intchannel.send(
                "Error while clearing channel.\n"
                "Missing permissions or messages too old."
            )
        else:
            await intchannel.send("Channel has been cleared.", delete_after=60)
        await intchannel.send(
            "Send suggestions here!\n"
            "Suggestions are accepted until the beginning of the vote.\n"
            "One suggestion/user, please! "
            "If you suggest more than one thing, "
            "all of the following suggestions will be ignored.\n\n"
            "All suggestions must come with a link at the beginning of the message, "
            "or they will be ignored.\n\n"
            "This thread is not for conversation."
        )

    logging.info(
        "Vote started in %s by %s at %s",
        str(cha),
        str(interaction.user),
        str(discord.utils.utcnow()),
    )
    config.lastvote = message
    config.channel = cha
    config.vote_running = True
    if polltime:
        config.closetime = timed
        logging.info("Vote will close at %s", str(timed))
        await discord.utils.sleep_until(timed)
        logging.info("Closing vote in %s due to polltime end.", str(cha))
        await endvote_internal("INTERNAL")  # type: ignore


@bot.tree.command(name="endvote", description="Ends vote.")
@app_commands.guild_only()
@app_commands.checks.has_any_role(config.role_id, config.owner_role)
@vote_running()
async def endvote(interaction: discord.Interaction) -> None:
    """This command is used to end a vote."""
    await endvote_internal(interaction)


async def endvote_internal(interaction: discord.Interaction) -> None:
    """This command is used to end a vote."""
    channel = config.channel
    submitted: List[str] = []
    vote: Dict[str, int] = {}
    usrlib: Dict[Union[discord.Member, discord.User], int] = {}
    disregarded: List[Union[discord.Member, discord.User]] = []
    disreg_votes: Dict[str, List[int]] = {}
    disreg_total: int = 0
    role = config.mention

    if interaction != "INTERNAL":
        oper = interaction.user
        await interaction.response.defer(thinking=True, ephemeral=True)
    else:
        oper = "system"

    await channel.send("Ending vote...", delete_after=60)
    votemsg = await config.lastvote

    if votemsg is None:
        raise app_commands.errors.AppCommandError("Vote message not found.")
    await votemsg.unpin()
    await channel.send(
        "Gathering votes and applying fraud protection... (This may take a while)"
    )

    async with channel.typing():
        if (
            votemsg.embeds
            and votemsg.embeds[0].description
            and votemsg.embeds[0].title == "Vote"
        ):
            for line in votemsg.embeds[0].description.splitlines():
                if " - " in line:
                    submitted.append(line.split(" - ")[1].lstrip("<").rstrip(">"))
        else:
            for line in votemsg.content.splitlines():
                if " - " in line:
                    submitted.append(line.split(" - ")[1].lstrip("<").rstrip(">"))
        timed = discord.utils.utcnow() - datetime.timedelta(days=31)

        async for message in channel.history(
            after=timed, oldest_first=True, limit=None
        ):
            if (
                message.author not in usrlib
                and message.author.id not in config.blacklist
            ):
                usrlib[message.author] = 1
            else:
                usrlib[message.author] += 1
        logging.debug("Submitted: %s", str(submitted))
        logging.debug("Users: %s", str(usrlib))

        for reaction in votemsg.reactions:
            if reaction.emoji in EMOJI_ALPHABET and EMOJI_ALPHABET.index(
                reaction.emoji
            ) < len(submitted):
                vote[reaction.emoji] = 0
                disreg_votes[reaction.emoji] = [0, 0, 0, 0]
                async for user in reaction.users():
                    flag_a = False
                    if user != bot.user and user in usrlib:
                        # Splitting up the if statement to avoid KeyErro
                        if usrlib[user] >= 5:
                            vote[reaction.emoji] += 1
                        else:
                            flag_a = True
                    elif user != bot.user and user.id not in config.blacklist:
                        flag_a = True

                    if flag_a:
                        disreg_total += 1
                        try:
                            usrlib_count = usrlib[user]
                        except KeyError:
                            usrlib_count = 0
                        disreg_votes[reaction.emoji][usrlib_count] += 1
                        if user not in disregarded:
                            disregarded.append(user)
                        logging.debug("Disregarded: %s", str(user))
        logging.debug("Votes: %s", str(vote))

    msg_text = "This week's featured results are:\n"
    for i in range(len(vote)):
        msg_text += (
            f"{EMOJI_ALPHABET[i]} - {vote[EMOJI_ALPHABET[i]]} vote"
            + f"{'s'[:vote[EMOJI_ALPHABET[i]]^1]}\n"
        )

    # Create an embed message with the voting results and send it to the channel
    results_embed = discord.Embed(title="RESULTS", description=msg_text, color=0x00FF00)
    await channel.send(embed=results_embed, reference=votemsg, mention_author=False)

    # Determine the candidate with the highest number of votes
    max_vote = max(vote.values())
    win_candidates = [k for k, v in vote.items() if v == max_vote]
    win_id = None
    tiebreak = 0

    # If there are multiple candidates with the same number of votes, apply tie-breaking rules
    if len(win_candidates) > 1:
        # Create a list of disregarded votes for each candidate
        disreg_ranges = list(zip(*[disreg_votes[c] for c in win_candidates]))
        discard_pile = []

        # Apply tie-breaking rules to determine the winner
        for batch in reversed(disreg_ranges):
            # Make a copy of the batch to avoid modifying the original
            tmp_set = list(deepcopy(batch))

            # Remove any indices that have already been discarded in previous iterations
            for i in discard_pile:
                tmp_set.pop(i)

            # If there is only one vote left in the batch, that candidate wins
            if len(tmp_set) == 1:
                win_id = win_candidates[batch.index(tmp_set[0])]
                tiebreak = 1
                break

            # Sort the votes in descending order and discard any votes that are lower than highest
            tmp_set.sort(reverse=True)
            for i in range(1, len(tmp_set)):
                if tmp_set[i] != tmp_set[0]:
                    discard_pile.append(batch.index(tmp_set[i]))
    else:
        win_id = win_candidates[0]

    # If there is still a tie, choose a winner randomly
    if win_id is None:
        tiebreak = 2
        win_id = choice(win_candidates)

    message_txt = (
        f"{role.mention} This week's featured results are in!\n"
        + f"The winner is {submitted[EMOJI_ALPHABET.index(win_id)]}"
        + f" with {vote[win_id]} vote{'s'[:vote[win_id]^1]}!"
    )

    if tiebreak == 1:
        message_txt += "\n\n(Tie-Break Rule 1: Highest disregarded votes)"
    elif tiebreak == 2:
        message_txt += "\n\n(Tie-Break Rule 2: Random)"

    message = await channel.send(message_txt)

    await message.add_reaction("🎉")
    await message.pin()

    if disregarded:
        fraport_text = (
            f"Total disregarded votes: {disreg_total}\n"
            + f"Total disregarded users: {len(disregarded)}\n"
            + "Disregarded users:\n"
        )
        for usr in disregarded:
            if usr in usrlib:
                fraport_text += (
                    f"{usr.mention} - {usrlib[usr]} message{'s'[:usrlib[usr]^1]}\n"
                )
            elif usr.id not in config.blacklist:
                fraport_text += f"{usr.mention} - Blacklisted\n"
            else:
                fraport_text += f"{usr.mention} - 0 messages\n"
        fraprot = discord.Embed(
            title="Fraud Protection Log", description=fraport_text, color=0xFC0303
        )
        fraprot.set_footer(text="This is a public safety announcement.")

    else:
        fraprot = discord.Embed(
            title="Fraud Protection Log",
            description="No users were disregarded.",
            color=0x00FFF7,
        )
        fraprot.set_footer(text="Thank you for your cooperation.")

    await channel.send(embed=fraprot)

    logging.info(
        "Vote ended in %s by %s at %s",
        str(channel),
        str(oper),
        str(discord.utils.utcnow()),
    )
    config.lastwin = message
    config.vote_running = False
    config.closetime = None
    if interaction != "INTERNAL":
        await interaction.followup.send("Vote ended.", ephemeral=True)


@bot.tree.command(name="autoclose", description="Sets the autoclose time.")
@app_commands.checks.has_any_role(config.role_id, config.owner_role)
@app_commands.describe(time="Time in hours.")
@vote_running()
async def autoclose(interaction: discord.Interaction, time: int = 24) -> None:
    """This command is used to configure the autoclose time."""
    timed = discord.utils.utcnow() + datetime.timedelta(hours=time)
    config.closetime = timed

    await interaction.response.send_message(
        f"Vote will close <t:{str(round(config.closetime_timestamp))}:R>.",
        ephemeral=True,
    )
    await discord.utils.sleep_until(timed)
    if not config.vote_running:
        logging.info("Vote already closed.")
        return
    await endvote_internal("INTERNAL")  # type: ignore


@bot.tree.command(name="blacklist", description="Blacklists a user.")
@app_commands.checks.has_any_role(config.role_id, config.owner_role)
async def blacklist(interaction: discord.Interaction, user: discord.User) -> None:
    """This command is used to blacklist a user from voting."""
    blacklst = config.blacklist
    if user.id in blacklst:
        blacklst.remove(user.id)
        await interaction.response.send_message(
            f"User {user.mention} unblacklisted.", ephemeral=True
        )
    else:
        blacklst.append(user.id)
        await interaction.response.send_message(
            f"User {user.mention} blacklisted.", ephemeral=True
        )
    config.blacklist = blacklst


@bot.tree.command(name="override", description="Tech's admin commands.")
@app_commands.describe(command="Command to use.")
@is_owner()
async def override(interaction: discord.Interaction, command: str) -> None:
    """This command is used to override the bot's commands."""
    await interaction.response.defer(thinking=True)
    logging.info("Owner override triggered: %s", command)

    if command == "reboot":
        logging.info("Rebooting...")
        await interaction.followup.send("Rebooting...")
        await bot.close()

    elif command == "pull":
        pull = await asyncio.create_subprocess_shell(
            "git pull",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=os.getcwd(),
        )
        stdo, stdr = await pull.communicate()
        await interaction.followup.send("Pulling...")
        if stdo:
            await interaction.followup.send(f"[stdout]\n{stdo.decode()}")
            logging.info("[stdout]\n%s", stdo.decode())

        if stdr:
            await interaction.followup.send(f"[stderr]\n{stdr.decode()}")
            logging.info("[stderr]\n%s", stdr.decode())

        await interaction.followup.send("Rebooting...")
        logging.info("Rebooting...")
        await bot.close()

    elif command == "debug":
        config.mode = "debug"
        logging.info("Rebooting with debug mode...")
        await interaction.followup.send("Debug mode enabling...")
        await bot.close()

    else:
        await interaction.followup.send("Invalid override command.")


@bot.tree.command(name="accessrole", description="Sets botrole.")
@app_commands.checks.has_any_role(465888032537444353, config.owner_role)
@app_commands.describe(addrole="Role to be set as botrole.")
async def accessrole(interaction: discord.Interaction, addrole: discord.Role) -> None:
    """Sets the <addrole> as the bot role."""
    config.role = addrole

    await interaction.response.send_message(
        f"Role {addrole} has been set as to have access.", ephemeral=True
    )


@bot.tree.command(name="setmention", description="Sets mention.")
@app_commands.checks.has_any_role(465888032537444353, config.owner_role)
@app_commands.describe(mention="Role to be set as mention.")
async def setmention(interaction: discord.Interaction, mention: discord.Role) -> None:
    """Sets the <mention> as the mention."""
    config.mention = mention

    await interaction.response.send_message(
        f"Role {mention} has been set to be mentioned.", ephemeral=True
    )

@bot.command()
@commands.dm_only()
@commands.is_owner()
async def sync(ctx: commands.Context):
    """Syncs the bot's slash commands."""
    await ctx.send("Syncing...")
    await bot.tree.sync()

def start():
    """Starts the bot."""
    bot.run(secret.token, log_handler=handler, root_logger=True)


if __name__ == "__main__":
    start()
