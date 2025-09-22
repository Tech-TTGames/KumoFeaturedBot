"""Custom checks for Discord commands."""
import discord
from discord import app_commands

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
    """Returns whether the user is the owner of the bot."""

    async def predicate(ctx: discord.Interaction):
        """The predicate for the check."""
        if ctx.user.id != 414075045678284810:
            raise app_commands.CheckFailure(
                "You are not the owner of this bot.")
        return True

    return app_commands.check(predicate)


def has_admin_role():
    """Check if user has admin role or is owner."""
    
    async def predicate(interaction: discord.Interaction):
        """The predicate for the check."""
        # Always allow owner
        if interaction.user.id == 414075045678284810:
            return True
            
        config = Config(interaction.client)
        try:
            # Check if user has the configured admin role
            if hasattr(config, 'role_id') and config.role_id:
                member = interaction.guild.get_member(interaction.user.id) if interaction.guild else None
                if member and any(role.id == config.role_id for role in member.roles):
                    return True
        except (ValueError, AttributeError):
            pass
            
        # Fallback to hardcoded role ID
        member = interaction.guild.get_member(interaction.user.id) if interaction.guild else None
        if member and any(role.id == 465888032537444353 for role in member.roles):
            return True
            
        raise app_commands.CheckFailure("You don't have permission to use this command.")
    
    return app_commands.check(predicate)