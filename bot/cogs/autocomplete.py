
"""
Emerald's Killfeed - Autocomplete System
Provides autocomplete functionality for Discord commands
"""

import logging
from typing import List

import discord
from discord.ext import commands

logger = logging.getLogger(__name__)

class ServerAutocomplete:
    """Autocomplete helper for server names"""
    
    @staticmethod
    async def autocomplete_server_name(ctx: discord.AutocompleteContext):
        """Autocomplete callback for server names"""
        try:
            guild_id = ctx.interaction.guild_id
            
            # Get bot instance from context
            bot = ctx.bot
            
            # Get guild configuration
            guild_config = await bot.db_manager.get_guild(guild_id)
            
            if not guild_config:
                return [discord.OptionChoice(name="No servers configured", value="none")]
                
            servers = guild_config.get('servers', [])
            
            if not servers:
                return [discord.OptionChoice(name="No servers found", value="none")]
            
            # Return server choices
            choices = []
            for server in servers[:25]:  # Discord limits to 25 choices
                server_id = str(server.get('_id', server.get('server_id', 'unknown')))
                server_name = server.get('name', server.get('server_name', f'Server {server_id}'))
                
                choices.append(discord.OptionChoice(
                    name=f"{server_name} (ID: {server_id})",
                    value=server_id
                ))
            
            return choices
            
        except Exception as e:
            logger.error(f"Autocomplete error: {e}")
            return [discord.OptionChoice(name="Error loading servers", value="none")]

class PlayerAutocomplete:
    """Autocomplete helper for player names"""
    
    @staticmethod
    async def autocomplete_player_name(ctx: discord.AutocompleteContext):
        """Autocomplete callback for player names"""
        try:
            guild_id = ctx.interaction.guild_id
            bot = ctx.bot
            
            # Get recent players from database
            cursor = bot.db_manager.pvp_data.find(
                {"guild_id": guild_id}, 
                {"player_name": 1}
            ).limit(25)
            
            players = []
            async for doc in cursor:
                player_name = doc.get('player_name')
                if player_name and player_name not in players:
                    players.append(player_name)
            
            # Create choices
            choices = [
                discord.OptionChoice(name=player, value=player)
                for player in sorted(players)[:25]
            ]
            
            return choices if choices else [discord.OptionChoice(name="No players found", value="none")]
            
        except Exception as e:
            logger.error(f"Player autocomplete error: {e}")
            return [discord.OptionChoice(name="Error loading players", value="none")]

def setup(bot):
    """Setup function for autocomplete helpers"""
    pass
