"""
Emerald's Killfeed - Faction System
Create and manage player factions
"""

import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

import discord
from discord.ext import commands
from bot.utils.embed_factory import EmbedFactory

logger = logging.getLogger(__name__)

class Factions(commands.Cog):
    """
    FACTIONS (PREMIUM)
    - Create and manage factions
    - Join/leave factions
    - Faction statistics and leaderboards
    """

    def __init__(self, bot):
        self.bot = bot

    async def check_premium_server(self, guild_id: int) -> bool:
        """Check if guild has premium access for faction features"""
        guild_doc = await self.bot.db_manager.get_guild(guild_id)
        if not guild_doc:
            return False

        servers = guild_doc.get('servers', [])
        for server_config in servers:
            server_id = server_config.get('server_id', server_config.get('_id', 'default'))
            if await self.bot.db_manager.is_premium_server(guild_id, server_id):
                return True

        return False

    async def get_user_faction(self, guild_id: int, discord_id: int) -> Optional[Dict[str, Any]]:
        """Get the faction a user belongs to"""
        return await self.bot.db_manager.factions.find_one({
            'guild_id': guild_id,
            'members': discord_id
        })

    async def autocomplete_faction_name(self, ctx: discord.AutocompleteContext):
        """Autocomplete callback for faction names"""
        try:
            guild_id = ctx.interaction.guild_id
            
            # Get all factions for this guild
            cursor = self.bot.db_manager.factions.find({'guild_id': guild_id}).sort('faction_name', 1)
            factions = await cursor.to_list(length=25)  # Limit to 25 for autocomplete
            
            # Return faction names for autocomplete
            return [
                discord.OptionChoice(
                    name=faction['faction_name'],
                    value=faction['faction_name']
                )
                for faction in factions
            ]
            
        except Exception as e:
            logger.error(f"Autocomplete error: {e}")
            return [discord.OptionChoice(name="Error loading factions", value="none")]

    async def calculate_faction_stats(self, guild_id: int, faction_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate combined stats for all faction members"""
        try:
            combined_stats = {
                'total_kills': 0,
                'total_deaths': 0,
                'total_suicides': 0,
                'total_kdr': 0.0,
                'member_count': len(faction_data['members']),
                'best_streak': 0,
                'total_distance': 0.0
            }

            # Get stats for all members
            for member_id in faction_data['members']:
                # Get member's linked characters
                player_data = await self.bot.db_manager.get_linked_player(guild_id, member_id)
                if not player_data:
                    continue

                # Get stats for each character across all servers
                for character in player_data['linked_characters']:
                    cursor = self.bot.db_manager.pvp_data.find({
                        'guild_id': guild_id,
                        'player_name': character
                    })

                    async for server_stats in cursor:
                        combined_stats['total_kills'] += server_stats.get('kills', 0)
                        combined_stats['total_deaths'] += server_stats.get('deaths', 0)
                        combined_stats['total_suicides'] += server_stats.get('suicides', 0)
                        combined_stats['total_distance'] += server_stats.get('total_distance', 0.0)

                        if server_stats.get('longest_streak', 0) > combined_stats['best_streak']:
                            combined_stats['best_streak'] = server_stats.get('longest_streak', 0)

            # Calculate faction KDR safely
            if combined_stats['total_deaths'] > 0:
                combined_stats['total_kdr'] = combined_stats['total_kills'] / combined_stats['total_deaths']
            else:
                combined_stats['total_kdr'] = float(combined_stats['total_kills'])

            return combined_stats

        except Exception as e:
            logger.error(f"Failed to calculate faction stats: {e}")
            return combined_stats

    @discord.slash_command(name="faction_create", description="Create a new faction")
    async def faction_create(self, ctx: discord.ApplicationContext, 
                           name: str, description: str = "A new faction"):
        """Create a new faction"""
        try:
            guild_id = ctx.guild.id
            discord_id = ctx.user.id

            # Check premium access
            if not await self.check_premium_server(guild_id):
                embed = EmbedFactory.build(
                    title="🔒 Premium Feature",
                    description="Faction system requires premium subscription!",
                    color=0xFF6B6B
                )
                await ctx.respond(embed=embed, ephemeral=True)
                return

            # Validate faction name
            if len(name) > 32:
                await ctx.respond("❌ Faction name too long! Maximum 32 characters.", ephemeral=True)
                return

            # Check if user already has a faction
            player_data = await self.bot.db_manager.get_linked_player(guild_id, discord_id)
            if player_data and player_data.get('faction'):
                await ctx.respond("❌ You're already in a faction! Leave your current faction first.", ephemeral=True)
                return

            # Create faction
            success = await self.bot.db_manager.create_faction(guild_id, name, description, discord_id)

            if success:
                embed = EmbedFactory.build(
                    title="⚔️ Faction Created",
                    description=f"Successfully created faction **{name}**",
                    color=0x00FF00,
                    timestamp=datetime.now(timezone.utc)
                )

                embed.add_field(
                    name="📝 Description",
                    value=description,
                    inline=False
                )

                embed.add_field(
                    name="👑 Leader",
                    value=ctx.user.mention,
                    inline=True
                )

                embed.add_field(
                    name="👥 Members",
                    value="1",
                    inline=True
                )

                await ctx.respond(embed=embed)
            else:
                await ctx.respond("❌ Failed to create faction. Name may already be taken.", ephemeral=True)

        except Exception as e:
            logger.error(f"Failed to create faction: {e}")
            await ctx.respond("❌ Failed to create faction.", ephemeral=True)

    @discord.slash_command(name="faction_info", description="View faction information")
    async def faction_info(self, ctx: discord.ApplicationContext, 
                          faction_name: str = None):
        """View information about a faction"""
        try:
            guild_id = ctx.guild.id
            discord_id = ctx.user.id

            # Check premium access
            if not await self.check_premium_server(guild_id):
                embed = EmbedFactory.build(
                    title="🔒 Premium Feature",
                    description="Faction system requires premium subscription!",
                    color=0xFF6B6B
                )
                await ctx.respond(embed=embed, ephemeral=True)
                return

            # If no faction specified, use user's faction
            if not faction_name:
                player_data = await self.bot.db_manager.get_linked_player(guild_id, discord_id)
                if not player_data or not player_data.get('faction'):
                    await ctx.respond("❌ You're not in a faction! Specify a faction name or join one first.", ephemeral=True)
                    return
                faction_name = player_data['faction']

            # Get faction info
            faction = await self.bot.db_manager.get_faction(guild_id, faction_name)

            if not faction:
                await ctx.respond(f"❌ Faction **{faction_name}** not found!", ephemeral=True)
                return

            embed = EmbedFactory.build(
                title=f"⚔️ {faction['name']}",
                description=faction['description'],
                color=0x9B59B6,
                timestamp=datetime.now(timezone.utc)
            )

            embed.add_field(
                name="👑 Leader",
                value=f"<@{faction['leader']}>",
                inline=True
            )

            embed.add_field(
                name="👥 Members",
                value=f"{len(faction['members'])}",
                inline=True
            )

            embed.add_field(
                name="📅 Created",
                value=f"<t:{int(faction['created_at'].timestamp())}:R>",
                inline=True
            )

            # Show some members
            if faction['members']:
                member_list = []
                for member_id in faction['members'][:5]:  # Show first 5
                    member_list.append(f"<@{member_id}>")

                if len(faction['members']) > 5:
                    member_list.append(f"... and {len(faction['members']) - 5} more")

                embed.add_field(
                    name="👥 Member List",
                    value="\n".join(member_list),
                    inline=False
                )

            await ctx.respond(embed=embed)

        except Exception as e:
            logger.error(f"Failed to show faction info: {e}")
            await ctx.respond("❌ Failed to retrieve faction information.", ephemeral=True)

def setup(bot):
    bot.add_cog(Factions(bot))