'''Bot setup module. Runs if config.json is not found.'''
import json
import logging

from discord.ext import commands

from variables import VERSION, Secret, handler, intents

bot = commands.Bot(command_prefix='.', intents=intents)
secret = Secret()

@bot.event
async def on_ready():
    """This event is called when the bot is ready to be used."""
    logging.info("%s has connected to Discord!", str(bot.user))

@bot.command(brief="Start setup.", description="Starts the setup process.")
@commands.check_any(commands.has_permissions(administrator=True),commands.is_owner())
async def setup(ctx):
    """Starts the setup process."""
    await ctx.send(f"Starting setup of KumoFeaturedBot {VERSION}...")
    confi = {}
    confi["mode"] = "prod"
    message = await ctx.author.send("Hello! I'm going to ask you a few questions to get started."
    " Use 'cancel' anytime to cancel the setup process.")
    dm_channel = message.channel

    def dm_from_user(msg):
        return msg.channel == dm_channel

    await dm_channel.send("Please select the prefix for the bot. (During setup, the prefix is '.')")
    prefi = await bot.wait_for('message', check=dm_from_user)
    confi["prefix"] = prefi.content

    await dm_channel.send("Please provide the ID of the Guild that the bot will function in:")
    while True: # Get guild ID
        gld = await bot.wait_for('message',check=dm_from_user)
        if gld.content.isnumeric():
            guild = bot.get_guild(int(gld.content))
            if guild is None:
                await dm_channel.send("That is not a valid Guild ID or I am not present there."
                "Please try again.")
            else:
                confi["guild"] = guild.id
                await dm_channel.send(f"Guild set to {guild.name}.")
                break

        else:
            if gld.content == 'cancel':
                return await dm_channel.send("Setup cancelled.")
            await dm_channel.send("That is not a valid Guild ID."
            " Please try again or use 'cancel' to cancel the setup.")

    await dm_channel.send("Please provide the ID of the channel that will be used for the bot:")
    while True: # Get channel ID
        chn = await bot.wait_for('message',check=dm_from_user)
        if chn.content.isnumeric():
            channel = guild.get_channel(int(chn.content))
            if channel is None:
                await dm_channel.send("That is not a valid channel ID or I am not present there."
                "Please try again.")
            else:
                confi["channel"] = channel.id
                await dm_channel.send(f"Channel set to {channel.mention}.")
                break

        else:
            if chn.content == 'cancel':
                return await dm_channel.send("Setup cancelled.")
            await dm_channel.send("That is not a valid channel ID."
            " Please try again or use 'cancel' to cancel the setup.")

    await dm_channel.send("Please provide the ID of the role that will be used for the bot users:")
    while True: # Get role ID
        rol = await bot.wait_for('message',check=dm_from_user)
        if rol.content.isnumeric():
            role = guild.get_role(int(rol.content))
            if role is None:
                await dm_channel.send("That is not a valid Role ID. Please try again.")
            else:
                confi["role"] = role.id
                await dm_channel.send(f"Role {role} has been set as the bot user role.")
                break

        else:
            if rol.content == 'cancel':
                return await dm_channel.send("Setup cancelled.")
            await dm_channel.send("That is not a valid Role ID."
            " Please try again or use 'cancel' to cancel the setup.")

    await dm_channel.send("Please provide the ID of the role that will be mentioned during votes:")
    while True: # Get role ID
        rol = await bot.wait_for('message',check=dm_from_user)
        if rol.content.isnumeric():
            role = guild.get_role(int(rol.content))
            if role is None:
                await dm_channel.send("That is not a valid Role ID. Please try again.")
            else:
                confi["mention"] = role.id
                await dm_channel.send(f"Role {role} has been set as the mention role.")
                break

        else:
            if rol.content == 'cancel':
                return await dm_channel.send("Setup cancelled.")
            await dm_channel.send("That is not a valid Role ID."
            " Please try again or use 'cancel' to cancel the setup.")

    await dm_channel.send("Preparing to save configuration...")
    confi["mention"] = None
    confi["lastvote"] = None
    confi["lastwin"] = None
    confi["closetime"] = None
    confi["voterunning"] = False
    with open('config.json', 'w+',encoding='utf-8') as config_file:
        json.dump(confi, config_file, indent=4)
        config_file.truncate()

    await dm_channel.send("Configuration saved. Setup complete.")
    await ctx.send("Setup complete. Restarting...")
    await bot.close()


def start():
    """Starts the bot."""
    bot.run(secret.token, log_handler=handler,root_logger=True)

if __name__ == '__main__':
    start()
