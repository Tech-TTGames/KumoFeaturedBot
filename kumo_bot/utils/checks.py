"""Custom checks for Discord commands."""
import discord
from discord import app_commands
from discord.ext import commands

from kumo_bot.config.settings import Config


def vote_running():
    """Returns whether a vote is running."""

    async def predicate(ctx: discord.Interaction):
        """The predicate for the check."""
        config = Config(ctx.client)
        if not config.vote_running or ctx.user == ctx.client.user:
            raise app_commands.CheckFailure("No vote is currently running.")
        return True

    return app_commands.check(predicate)


def is_owner():
    """Returns whether the user is the owner of the bot using Discord.py app owner data."""

    async def predicate(ctx: discord.Interaction):
        """The predicate for the check."""
        app_info = await ctx.client.application_info()
        if app_info.team:
            # Bot is owned by a team
            is_team_owner = ctx.user.id in [member.id for member in app_info.team.members]
        else:
            # Bot is owned by a single user
            is_team_owner = ctx.user.id == app_info.owner.id
            
        if not is_team_owner:
            raise app_commands.CheckFailure("You are not the owner of this bot.")
        return True

    return app_commands.check(predicate)


def has_admin_role():
    """Check if user has admin role, Administrator permission, or is owner."""
    
    async def predicate(interaction: discord.Interaction):
        """The predicate for the check."""
        # Always allow app owner(s)
        app_info = await interaction.client.application_info()
        if app_info.team:
            # Bot is owned by a team
            if interaction.user.id in [member.id for member in app_info.team.members]:
                return True
        else:
            # Bot is owned by a single user
            if interaction.user.id == app_info.owner.id:
                return True
        
        # Check if user has Administrator permission
        if interaction.guild:
            member = interaction.guild.get_member(interaction.user.id)
            if member and member.guild_permissions.administrator:
                return True
        
        # Check if user has the configured admin role
        config = Config(interaction.client)
        try:
            if hasattr(config, 'role_id') and config.role_id:
                member = interaction.guild.get_member(interaction.user.id) if interaction.guild else None
                if member and any(role.id == config.role_id for role in member.roles):
                    return True
        except (ValueError, AttributeError):
            pass
            
        raise app_commands.CheckFailure("You don't have permission to use this command.")
    
    return app_commands.check(predicate)