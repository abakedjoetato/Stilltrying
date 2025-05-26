
"""
Emerald's Killfeed - Leaderboards System
Fixed version with proper py-cord 2.6.1 syntax
"""

import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

import discord
from discord.ext import commands
from bot.utils.embed_factory import EmbedFactory

logger = logging.getLogger(__name__)

class LeaderboardsFixed(commands.Cog):
    """
    LEADERBOARDS (PREMIUM)
    - Top players by kills, KDR, streak
    - Server-specific and guild-wide stats
    """
    
    def __init__(self, bot):
        self.bot = bot
    
    async def check_premium_server(self, guild_id: int) -> bool:
        """Check if guild has premium access for leaderboard features"""
        guild_doc = await self.bot.db_manager.get_guild(guild_id)
        if not guild_doc:
            return False
        
        servers = guild_doc.get('servers', [])
        for server_config in servers:
            server_id = server_config.get('server_id', server_config.get('_id', 'default'))
            if await self.bot.db_manager.is_premium_server(guild_id, server_id):
                return True
        
        return False
    
    @commands.slash_command(name="leaderboard", description="View player leaderboards")
    async def leaderboard(self, ctx: discord.ApplicationContext, 
                         board_type: discord.Option(str, "Type of leaderboard", 
                                                   choices=["kills", "kdr", "streak", "distance"])):
        """Display leaderboards for various stats"""
        try:
            guild_id = ctx.guild.id
            
            # Check premium access
            if not await self.check_premium_server(guild_id):
                embed = discord.Embed(
                    title="🔒 Premium Feature",
                    description="Leaderboards require premium subscription!",
                    color=0xFF6B6B
                )
                await ctx.respond(embed=embed, ephemeral=True)
                return
            
            await ctx.defer()
            
            # Get leaderboard data based on type
            leaderboard_data = await self._get_leaderboard_data(guild_id, board_type)
            
            if not leaderboard_data:
                embed = discord.Embed(
                    title=f"📊 {board_type.title()} Leaderboard",
                    description="No data available yet!",
                    color=0x808080,
                    timestamp=datetime.now(timezone.utc)
                )
                await ctx.followup.send(embed=embed)
                return
            
            # Create leaderboard embed
            embed = discord.Embed(
                title=f"🏆 {board_type.title()} Leaderboard",
                description=f"Top players by {board_type}",
                color=0xFFD700,
                timestamp=datetime.now(timezone.utc)
            )
            
            # Format leaderboard entries
            leaderboard_text = []
            for i, entry in enumerate(leaderboard_data[:10], 1):  # Top 10
                medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
                
                player_name = entry['player_name']
                value = entry['value']
                
                if board_type == "kdr":
                    value_text = f"{value:.2f}"
                elif board_type == "distance":
                    value_text = f"{value:,.1f}m"
                else:
                    value_text = f"{value:,}"
                
                leaderboard_text.append(f"{medal} **{player_name}** - {value_text}")
            
            embed.add_field(
                name="📋 Rankings",
                value="\n".join(leaderboard_text),
                inline=False
            )
            
            embed.set_thumbnail(url="attachment://Leaderboard.png")
            embed.set_footer(text="Powered by Discord.gg/EmeraldServers")
            
            await ctx.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Failed to show leaderboard: {e}")
            await ctx.respond("❌ Failed to retrieve leaderboard data.", ephemeral=True)
    
    async def _get_leaderboard_data(self, guild_id: int, board_type: str) -> List[Dict[str, Any]]:
        """Get leaderboard data from database"""
        try:
            pipeline = []
            
            # Match guild
            pipeline.append({"$match": {"guild_id": guild_id}})
            
            # Group by player and calculate totals
            if board_type == "kills":
                pipeline.extend([
                    {"$group": {
                        "_id": "$player_name",
                        "total_kills": {"$sum": "$kills"}
                    }},
                    {"$sort": {"total_kills": -1}},
                    {"$project": {
                        "player_name": "$_id",
                        "value": "$total_kills",
                        "_id": 0
                    }}
                ])
            elif board_type == "kdr":
                pipeline.extend([
                    {"$group": {
                        "_id": "$player_name",
                        "total_kills": {"$sum": "$kills"},
                        "total_deaths": {"$sum": "$deaths"}
                    }},
                    {"$match": {"total_deaths": {"$gt": 0}}},  # Only players with deaths
                    {"$addFields": {
                        "kdr": {"$divide": ["$total_kills", "$total_deaths"]}
                    }},
                    {"$sort": {"kdr": -1}},
                    {"$project": {
                        "player_name": "$_id",
                        "value": "$kdr",
                        "_id": 0
                    }}
                ])
            elif board_type == "streak":
                pipeline.extend([
                    {"$group": {
                        "_id": "$player_name",
                        "best_streak": {"$max": "$longest_streak"}
                    }},
                    {"$sort": {"best_streak": -1}},
                    {"$project": {
                        "player_name": "$_id",
                        "value": "$best_streak",
                        "_id": 0
                    }}
                ])
            elif board_type == "distance":
                pipeline.extend([
                    {"$group": {
                        "_id": "$player_name",
                        "total_distance": {"$sum": "$total_distance"}
                    }},
                    {"$sort": {"total_distance": -1}},
                    {"$project": {
                        "player_name": "$_id",
                        "value": "$total_distance",
                        "_id": 0
                    }}
                ])
            
            # Execute aggregation
            cursor = self.bot.db_manager.pvp_data.aggregate(pipeline)
            results = await cursor.to_list(length=50)  # Get top 50
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to get leaderboard data: {e}")
            return []

def setup(bot):
    bot.add_cog(LeaderboardsFixed(bot))
