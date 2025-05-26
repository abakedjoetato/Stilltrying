"""
Emerald's Killfeed - Player Statistics System
Display player stats, weapon stats, and performance metrics
"""

import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

import discord
from discord.ext import commands
from bot.utils.embed_factory import EmbedFactory

logger = logging.getLogger(__name__)

class Stats(commands.Cog):
    """
    STATS (FREE)
    - Player statistics and performance metrics
    - Weapon statistics
    - Kill/death ratios and streaks
    """

    def __init__(self, bot):
        self.bot = bot

    @discord.slash_command(name="stats", description="View player statistics")
    async def stats(self, ctx: discord.ApplicationContext, 
                   player: discord.Option(str, "Player name", required=False)):
        """Display player statistics"""
        try:
            guild_id = ctx.guild.id
            discord_id = ctx.user.id

            # If no player specified, use linked character
            if not player:
                player_data = await self.bot.db_manager.get_linked_player(guild_id, discord_id)
                if not player_data:
                    await ctx.respond(
                        "❌ No player specified and you don't have any linked characters! Use `/link <character>` first.",
                        ephemeral=True
                    )
                    return
                player = player_data['primary_character']

            # Get player stats
            stats = await self.bot.db_manager.get_player_stats(guild_id, player)

            if not stats:
                embed = EmbedFactory.build(
                    title="📊 Player Statistics",
                    description=f"No statistics found for **{player}**",
                    color=0x808080
                )
                await ctx.respond(embed=embed)
                return

            # Calculate KDR
            kdr = stats['kills'] / max(stats['deaths'], 1)

            embed = EmbedFactory.build(
                title="📊 Player Statistics",
                description=f"Performance metrics for **{player}**",
                color=0x3498DB,
                timestamp=datetime.now(timezone.utc)
            )

            embed.add_field(
                name="⚔️ Combat Stats",
                value=f"• Kills: **{stats['kills']:,}**\n• Deaths: **{stats['deaths']:,}**\n• K/D Ratio: **{kdr:.2f}**",
                inline=True
            )

            embed.add_field(
                name="🎯 Performance",
                value=f"• Best Streak: **{stats.get('longest_streak', 0)}**\n• Current Streak: **{stats.get('current_streak', 0)}**\n• Distance: **{stats.get('total_distance', 0):,.1f}m**",
                inline=True
            )

            embed.add_field(
                name="📅 Activity",
                value=f"• Last Seen: <t:{int(stats.get('last_seen', datetime.now()).timestamp())}:R>\n• First Seen: <t:{int(stats.get('first_seen', datetime.now()).timestamp())}:R>",
                inline=False
            )

            await ctx.respond(embed=embed)

        except Exception as e:
            logger.error(f"Failed to show stats: {e}")
            await ctx.respond("❌ Failed to retrieve player statistics.", ephemeral=True)

def setup(bot):
    bot.add_cog(Stats(bot))