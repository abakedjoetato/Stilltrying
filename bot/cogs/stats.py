
"""
Emerald's Killfeed - Player Statistics (PHASE 2)
Player stats, server stats, weapon stats
"""

import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any

import discord
from discord.ext import commands
from bot.utils.embed_factory import EmbedFactory

logger = logging.getLogger(__name__)

class Stats(commands.Cog):
    """
    PLAYER STATISTICS (PREMIUM)
    - /player, /server, /weapon
    - Detailed PvP analytics
    """

    def __init__(self, bot):
        self.bot = bot

    @discord.slash_command(name="player", description="Get detailed player statistics")
    async def player_stats(
        self, 
        ctx: discord.ApplicationContext,
        player_name: discord.Option(str, "Player name to lookup", required=True)
    ):
        """Display detailed player statistics"""
        try:
            # Get player data from database
            db = self.bot.database
            player_data = await db.players.find_one({"name": player_name})
            
            if not player_data:
                embed = EmbedFactory.build(
                    embed_type="error",
                    title="❌ Player Not Found",
                    description=f"No statistics found for player: `{player_name}`"
                )
                await ctx.respond(embed=embed, ephemeral=True)
                return

            # Build player stats embed
            embed_data = {
                'title': f'📊 Player Statistics: {player_name}',
                'description': 'Detailed player performance metrics',
                'thumbnail_url': 'attachment://main.png',
                'fields': [
                    {
                        'name': '🎯 Combat Stats',
                        'value': f"• Kills: **{player_data.get('kills', 0)}**\n• Deaths: **{player_data.get('deaths', 0)}**\n• K/D Ratio: **{player_data.get('kdr', 0.0):.2f}**",
                        'inline': True
                    },
                    {
                        'name': '💰 Economy',
                        'value': f"• Balance: **${player_data.get('balance', 0):,}**\n• Total Earned: **${player_data.get('total_earned', 0):,}**",
                        'inline': True
                    },
                    {
                        'name': '⏱️ Activity',
                        'value': f"• Playtime: **{player_data.get('playtime_hours', 0)} hours**\n• Last Seen: **{player_data.get('last_seen', 'Unknown')}**",
                        'inline': True
                    }
                ]
            }
            
            embed = EmbedFactory.build("stats", embed_data)
            await ctx.respond(embed=embed)

        except Exception as e:
            logger.error(f"Failed to get player stats: {e}")
            embed = EmbedFactory.build(
                embed_type="error",
                title="❌ Error",
                description="Failed to retrieve player statistics."
            )
            await ctx.respond(embed=embed, ephemeral=True)

    @discord.slash_command(name="server", description="Get server statistics and leaderboards")
    async def server_stats(self, ctx: discord.ApplicationContext):
        """Display server-wide statistics"""
        try:
            db = self.bot.database
            
            # Get server stats
            total_players = await db.players.count_documents({})
            total_kills = await db.killfeeds.count_documents({})
            
            # Get top players
            top_killers = await db.players.find({}).sort("kills", -1).limit(5).to_list(5)
            
            embed_data = {
                'title': '🌐 Server Statistics',
                'description': 'Overall server performance metrics',
                'thumbnail_url': 'attachment://main.png',
                'fields': [
                    {
                        'name': '📊 General Stats',
                        'value': f"• Total Players: **{total_players:,}**\n• Total Kills: **{total_kills:,}**\n• Active Sessions: **{len(self.bot.guilds)}**",
                        'inline': True
                    },
                    {
                        'name': '🏆 Top Killers',
                        'value': '\n'.join([f"{i+1}. **{p['name']}** - {p.get('kills', 0)} kills" for i, p in enumerate(top_killers)]) or "No data available",
                        'inline': True
                    }
                ]
            }
            
            embed = EmbedFactory.build("stats", embed_data)
            await ctx.respond(embed=embed)

        except Exception as e:
            logger.error(f"Failed to get server stats: {e}")
            embed = EmbedFactory.build(
                embed_type="error",
                title="❌ Error",
                description="Failed to retrieve server statistics."
            )
            await ctx.respond(embed=embed, ephemeral=True)

    @discord.slash_command(name="weapon", description="Get weapon usage statistics")
    async def weapon_stats(
        self,
        ctx: discord.ApplicationContext,
        weapon_name: discord.Option(str, "Weapon name to analyze", required=False)
    ):
        """Display weapon usage statistics"""
        try:
            db = self.bot.database
            
            if weapon_name:
                # Get specific weapon stats
                weapon_kills = await db.killfeeds.count_documents({"weapon": weapon_name})
                
                embed_data = {
                    'title': f'🔫 Weapon Stats: {weapon_name}',
                    'description': f'Usage statistics for {weapon_name}',
                    'thumbnail_url': 'attachment://main.png',
                    'fields': [
                        {
                            'name': '📊 Usage Stats',
                            'value': f"• Total Kills: **{weapon_kills:,}**\n• Popularity Rank: **TBD**",
                            'inline': True
                        }
                    ]
                }
            else:
                # Get top weapons
                pipeline = [
                    {"$group": {"_id": "$weapon", "kills": {"$sum": 1}}},
                    {"$sort": {"kills": -1}},
                    {"$limit": 10}
                ]
                
                top_weapons = await db.killfeeds.aggregate(pipeline).to_list(10)
                
                weapon_list = '\n'.join([
                    f"{i+1}. **{w['_id']}** - {w['kills']} kills" 
                    for i, w in enumerate(top_weapons)
                ]) or "No weapon data available"
                
                embed_data = {
                    'title': '🔫 Top Weapons',
                    'description': 'Most used weapons on the server',
                    'thumbnail_url': 'attachment://main.png',
                    'fields': [
                        {
                            'name': '🏆 Weapon Rankings',
                            'value': weapon_list,
                            'inline': False
                        }
                    ]
                }
            
            embed = EmbedFactory.build("stats", embed_data)
            await ctx.respond(embed=embed)

        except Exception as e:
            logger.error(f"Failed to get weapon stats: {e}")
            embed = EmbedFactory.build(
                embed_type="error", 
                title="❌ Error",
                description="Failed to retrieve weapon statistics."
            )
            await ctx.respond(embed=embed, ephemeral=True)

def setup(bot):
    bot.add_cog(Stats(bot))
