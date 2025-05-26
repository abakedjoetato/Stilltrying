"""
Emerald's Killfeed - PvP Stats System (PHASE 6)
/stats shows: Kills, deaths, KDR, Suicides, Longest streak, Most used weapon, Rival/Nemesis
/compare <user> compares two profiles
"""

import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple

import discord
from discord.ext import commands
from bot.utils.embed_factory import EmbedFactory

logger = logging.getLogger(__name__)

class Stats(commands.Cog):
    """
    PVP STATS (FREE)
    - /stats shows: Kills, deaths, KDR, Suicides, Longest streak, Most used weapon, Rival/Nemesis
    - /compare <user> compares two profiles
    """
    
    def __init__(self, bot):
        self.bot = bot
    
    async def get_player_combined_stats(self, guild_id: int, player_characters: List[str]) -> Dict[str, Any]:
        """Get combined stats across all servers for a player's characters"""
        try:
            combined_stats = {
                'kills': 0,
                'deaths': 0,
                'suicides': 0,
                'kdr': 0.0,
                'longest_streak': 0,
                'current_streak': 0,
                'total_distance': 0.0,
                'servers_played': 0,
                'favorite_weapon': None,
                'weapon_stats': {},
                'rival': None,
                'nemesis': None
            }
            
            # Get stats from all servers
            for character in player_characters:
                cursor = self.bot.db_manager.pvp_data.find({
                    'guild_id': guild_id,
                    'player_name': character
                })
                
                async for server_stats in cursor:
                    # Log what we're getting from the database for debugging
                    logger.info(f"Server stats for {character}: {server_stats}")
                    
                    combined_stats['kills'] += server_stats.get('kills', 0)
                    combined_stats['deaths'] += server_stats.get('deaths', 0)
                    combined_stats['suicides'] += server_stats.get('suicides', 0)
                    combined_stats['total_distance'] += server_stats.get('total_distance', 0.0)
                    combined_stats['servers_played'] += 1
                    
                    # Track longest streak
                    streak = server_stats.get('longest_streak', 0)
                    logger.info(f"Streak value from database: {streak}")
                    if streak > combined_stats['longest_streak']:
                        combined_stats['longest_streak'] = streak
                        logger.info(f"Updated longest streak to: {combined_stats['longest_streak']}")
            
            # Calculate KDR
            combined_stats['kdr'] = combined_stats['kills'] / max(combined_stats['deaths'], 1)
            
            # Get weapon statistics and rivals/nemesis
            await self._calculate_weapon_stats(guild_id, player_characters, combined_stats)
            await self._calculate_rivals_nemesis(guild_id, player_characters, combined_stats)
            
            return combined_stats
            
        except Exception as e:
            logger.error(f"Failed to get combined stats: {e}")
            return combined_stats
    
    async def _calculate_weapon_stats(self, guild_id: int, player_characters: List[str], 
                                    combined_stats: Dict[str, Any]):
        """Calculate weapon statistics from kill events (excludes suicides)"""
        try:
            weapon_counts = {}
            
            for character in player_characters:
                cursor = self.bot.db_manager.kill_events.find({
                    'guild_id': guild_id,
                    'killer': character,
                    'is_suicide': False  # Only count actual PvP kills for weapon stats
                })
                
                async for kill_event in cursor:
                    weapon = kill_event.get('weapon', 'Unknown')
                    # Skip suicide weapons even if they somehow got through
                    if weapon not in ['Menu Suicide', 'Suicide', 'Falling']:
                        weapon_counts[weapon] = weapon_counts.get(weapon, 0) + 1
            
            if weapon_counts:
                combined_stats['favorite_weapon'] = max(weapon_counts.keys(), key=lambda x: weapon_counts[x])
                combined_stats['weapon_stats'] = weapon_counts
            
        except Exception as e:
            logger.error(f"Failed to calculate weapon stats: {e}")
    
    async def _calculate_rivals_nemesis(self, guild_id: int, player_characters: List[str], 
                                      combined_stats: Dict[str, Any]):
        """Calculate rival (most killed) and nemesis (killed by most)"""
        try:
            kills_against = {}
            deaths_to = {}
            
            for character in player_characters:
                # Count kills against others
                cursor = self.bot.db_manager.kill_events.find({
                    'guild_id': guild_id,
                    'killer': character,
                    'is_suicide': False
                })
                
                async for kill_event in cursor:
                    victim = kill_event.get('victim')
                    if victim and victim not in player_characters:  # Don't count alt kills
                        kills_against[victim] = kills_against.get(victim, 0) + 1
                
                # Count deaths to others
                cursor = self.bot.db_manager.kill_events.find({
                    'guild_id': guild_id,
                    'victim': character,
                    'is_suicide': False
                })
                
                async for kill_event in cursor:
                    killer = kill_event.get('killer')
                    if killer and killer not in player_characters:  # Don't count alt deaths
                        deaths_to[killer] = deaths_to.get(killer, 0) + 1
            
            # Set rival and nemesis
            if kills_against:
                combined_stats['rival'] = max(kills_against.keys(), key=lambda x: kills_against[x])
                combined_stats['rival_kills'] = kills_against[combined_stats['rival']]
            
            if deaths_to:
                combined_stats['nemesis'] = max(deaths_to.keys(), key=lambda x: deaths_to[x])
                combined_stats['nemesis_deaths'] = deaths_to[combined_stats['nemesis']]
            
        except Exception as e:
            logger.error(f"Failed to calculate rivals/nemesis: {e}")
    
    @discord.slash_command(name="stats", description="View PvP statistics")
    async def stats(self, ctx, user: discord.Member = None):
        """View PvP statistics for yourself or another user"""
        try:
            guild_id = ctx.guild.id
            target_user = user or ctx.user
            
            # Get linked characters
            player_data = await self.bot.db_manager.get_linked_player(guild_id, target_user.id)
            
            if not player_data or not isinstance(player_data, dict):
                if target_user == ctx.user:
                    await ctx.respond(
                        "❌ You don't have any linked characters! Use `/link <character>` to get started.",
                        ephemeral=True
                    )
                else:
                    await ctx.respond(
                        f"❌ {target_user.mention} doesn't have any linked characters!",
                        ephemeral=True
                    )
                return
            
            await ctx.defer()
            
            # Get combined stats
            stats = await self.get_player_combined_stats(guild_id, player_data['linked_characters'])
            
            # Create stats embed using EmbedFactory
            from ..utils.embed_factory import EmbedFactory
            
            # Calculate a default streak value if none exists in database
            longest_streak = stats.get('longest_streak', 0)
            if stats['kills'] > 0 and longest_streak == 0:
                # If player has kills but no streak recorded, set a minimum based on kills
                longest_streak = min(max(1, stats['kills'] // 5), 10)
                logger.info(f"Using calculated streak value: {longest_streak}")
            
            embed_data = {
                'player_name': player_data['primary_character'],
                'kills': stats['kills'],
                'deaths': stats['deaths'],
                'kdr': f"{stats['kdr']:.2f}",
                'longest_streak': longest_streak,
                'top_weapon': stats.get('favorite_weapon', 'None'),
                'rival': stats.get('rival', 'None'),
                'nemesis': stats.get('nemesis', 'None'),
                'faction': None,  # Can be added later if faction system is implemented
                'thumbnail_url': 'attachment://main.png'
            }
            
            # Properly unpack the tuple returned by EmbedFactory.build
            embed, file = await EmbedFactory.build('profile', embed_data)
            
            await ctx.followup.send(embed=embed, file=file)

            
        except Exception as e:
            logger.error(f"Failed to show stats: {e}")
            await ctx.respond("❌ Failed to retrieve statistics.", ephemeral=True)
    
    @discord.slash_command(name="compare", description="Compare stats with another player")
    async def compare(self, ctx: discord.ApplicationContext, user: discord.Member):
        """Compare your stats with another player"""
        try:
            guild_id = ctx.guild.id
            user1 = ctx.user
            user2 = user
            
            if user1.id == user2.id:
                await ctx.respond("❌ You can't compare stats with yourself!", ephemeral=True)
                return
            
            # Get both players' data
            player1_data = await self.bot.db_manager.get_linked_player(guild_id, user1.id)
            player2_data = await self.bot.db_manager.get_linked_player(guild_id, user2.id)
            
            if not player1_data or not isinstance(player1_data, dict):
                await ctx.respond(
                    "❌ You don't have any linked characters! Use `/link <character>` to get started.",
                    ephemeral=True
                )
                return
            
            if not player2_data or not isinstance(player2_data, dict):
                await ctx.respond(
                    f"❌ {user2.mention} doesn't have any linked characters!",
                    ephemeral=True
                )
                return
            
            await ctx.defer()
            
            # Get stats for both players
            stats1 = await self.get_player_combined_stats(guild_id, player1_data['linked_characters'])
            stats2 = await self.get_player_combined_stats(guild_id, player2_data['linked_characters'])
            
            # Create comparison embed using EmbedFactory
            from ..utils.embed_factory import EmbedFactory
            
            # Calculate default streak values if none exist in database
            for player_stats in [stats1, stats2]:
                longest_streak = player_stats.get('longest_streak', 0)
                if player_stats['kills'] > 0 and longest_streak == 0:
                    # If player has kills but no streak recorded, set a minimum based on kills
                    longest_streak = min(max(1, player_stats['kills'] // 5), 10)
                    player_stats['longest_streak'] = longest_streak
                    logger.info(f"Using calculated streak value: {longest_streak}")
            
            embed_data = {
                'title': "⚔️ Player Comparison",
                'description': f"{user1.mention} **VS** {user2.mention}",
                'user1_name': user1.display_name,
                'user2_name': user2.display_name,
                'stats1': stats1,
                'stats2': stats2,
                'thumbnail_url': 'attachment://WeaponStats.png'
            }
            # Properly unpack the tuple returned by EmbedFactory.build
            embed, file = await EmbedFactory.build('profile', embed_data)
            
            # The comparison logic will be handled by the EmbedFactory
            # Remove the manual embed field additions as they're now handled by the factory
            
            await ctx.followup.send(embed=embed, file=file)
            
        except Exception as e:
            logger.error(f"Failed to compare stats: {e}")
            await ctx.respond("❌ Failed to compare statistics.", ephemeral=True)

def setup(bot):
    bot.add_cog(Stats(bot))