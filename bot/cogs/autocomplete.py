
"""
Emerald's Killfeed - Autocomplete Utilities
Provides autocomplete functionality for various commands
"""

import logging
from typing import List, Dict, Any, Optional

import discord
from discord.ext import commands

logger = logging.getLogger(__name__)

class Autocomplete(commands.Cog):
    """
    AUTOCOMPLETE UTILITIES
    - Server autocomplete
    - Player autocomplete
    - Character autocomplete
    """

    def __init__(self, bot):
        self.bot = bot

    async def get_servers_for_guild(self, guild_id: int) -> List[Dict[str, Any]]:
        """Get all servers configured for a guild"""
        try:
            guild_doc = await self.bot.db_manager.get_guild(guild_id)
            if not guild_doc:
                return []
            
            servers = guild_doc.get('servers', [])
            return servers
            
        except Exception as e:
            logger.error(f"Failed to get servers for guild {guild_id}: {e}")
            return []

    async def get_players_for_server(self, guild_id: int, server_id: str = "default") -> List[str]:
        """Get all players for a specific server"""
        try:
            players = await self.bot.db_manager.db.players.find({
                "guild_id": guild_id,
                "server_id": server_id
            }).to_list(None)
            
            player_names = []
            for player in players:
                if 'character_name' in player:
                    player_names.append(player['character_name'])
            
            return sorted(list(set(player_names)))
            
        except Exception as e:
            logger.error(f"Failed to get players for server {server_id}: {e}")
            return []

    async def get_characters_for_discord_user(self, guild_id: int, discord_id: int) -> List[str]:
        """Get all characters for a Discord user"""
        try:
            links = await self.bot.db_manager.db.player_links.find({
                "guild_id": guild_id,
                "discord_id": discord_id
            }).to_list(None)
            
            characters = []
            for link in links:
                if 'character_name' in link:
                    characters.append(link['character_name'])
            
            return sorted(list(set(characters)))
            
        except Exception as e:
            logger.error(f"Failed to get characters for Discord user {discord_id}: {e}")
            return []

    async def server_autocomplete(self, ctx: discord.AutocompleteContext) -> List[discord.OptionChoice]:
        """Autocomplete for server selection"""
        try:
            guild_id = ctx.interaction.guild.id
            servers = await self.get_servers_for_guild(guild_id)
            
            choices = []
            for server in servers:
                server_id = server.get('server_id', server.get('_id', 'default'))
                server_name = server.get('server_name', f'Server {server_id}')
                
                # Filter based on current input
                if not ctx.value or ctx.value.lower() in server_name.lower():
                    choices.append(discord.OptionChoice(
                        name=server_name,
                        value=server_id
                    ))
            
            return choices[:25]  # Discord limit
            
        except Exception as e:
            logger.error(f"Server autocomplete error: {e}")
            return []

    async def player_autocomplete(self, ctx: discord.AutocompleteContext) -> List[discord.OptionChoice]:
        """Autocomplete for player selection"""
        try:
            guild_id = ctx.interaction.guild.id
            
            # Try to get server_id from other options
            server_id = "default"
            if hasattr(ctx, 'options') and 'server_id' in ctx.options:
                server_id = ctx.options['server_id']
            
            players = await self.get_players_for_server(guild_id, server_id)
            
            choices = []
            for player in players:
                # Filter based on current input
                if not ctx.value or ctx.value.lower() in player.lower():
                    choices.append(discord.OptionChoice(
                        name=player,
                        value=player
                    ))
            
            return choices[:25]  # Discord limit
            
        except Exception as e:
            logger.error(f"Player autocomplete error: {e}")
            return []

    async def character_autocomplete(self, ctx: discord.AutocompleteContext) -> List[discord.OptionChoice]:
        """Autocomplete for character selection"""
        try:
            guild_id = ctx.interaction.guild.id
            discord_id = ctx.interaction.user.id
            
            characters = await self.get_characters_for_discord_user(guild_id, discord_id)
            
            choices = []
            for character in characters:
                # Filter based on current input
                if not ctx.value or ctx.value.lower() in character.lower():
                    choices.append(discord.OptionChoice(
                        name=character,
                        value=character
                    ))
            
            return choices[:25]  # Discord limit
            
        except Exception as e:
            logger.error(f"Character autocomplete error: {e}")
            return []

def setup(bot):
    bot.add_cog(Autocomplete(bot))
