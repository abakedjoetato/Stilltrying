"""
Emerald's Killfeed - Parser Management System
Manage killfeed parsing, log processing, and data collection
"""

import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any

import discord
from discord.ext import commands
from bot.cogs.autocomplete import ServerAutocomplete

logger = logging.getLogger(__name__)

class Parsers(commands.Cog):
    """
    PARSER MANAGEMENT
    - Killfeed parser controls
    - Log processing management
    - Data collection status
    """
    
    def __init__(self, bot):
        self.bot = bot
    
    @commands.slash_command(name="parser", description="Parser management commands")
    async def parser(self, ctx: discord.ApplicationContext):
        """Base parser command"""
        pass
    
    @parser.command(name="status", description="Check parser status")
    async def parser_status(self, ctx: discord.ApplicationContext):
        """Check the status of all parsers"""
        try:
            embed = discord.Embed(
                title="🔍 Parser Status",
                description="Current status of all data parsers",
                color=0x3498DB,
                timestamp=datetime.now(timezone.utc)
            )
            
            # Killfeed parser status
            killfeed_status = "🟢 Active" if hasattr(self.bot, 'killfeed_parser') and self.bot.killfeed_parser else "🔴 Inactive"
            
            # Log parser status
            log_status = "🟢 Active" if hasattr(self.bot, 'log_parser') and self.bot.log_parser else "🔴 Inactive"
            
            # Historical parser status
            historical_status = "🟢 Active" if hasattr(self.bot, 'historical_parser') and self.bot.historical_parser else "🔴 Inactive"
            
            embed.add_field(
                name="📡 Killfeed Parser",
                value=f"Status: **{killfeed_status}**\nMonitors live PvP events",
                inline=True
            )
            
            embed.add_field(
                name="📜 Log Parser",
                value=f"Status: **{log_status}**\nProcesses server log files",
                inline=True
            )
            
            embed.add_field(
                name="📚 Historical Parser",
                value=f"Status: **{historical_status}**\nRefreshes historical data",
                inline=True
            )
            
            # Scheduler status
            scheduler_status = "🟢 Running" if self.bot.scheduler.running else "🔴 Stopped"
            embed.add_field(
                name="⏰ Background Scheduler",
                value=f"Status: **{scheduler_status}**\nManages automated tasks",
                inline=False
            )
            
            embed.set_thumbnail(url="attachment://main.png")
            embed.set_footer(text="Powered by Discord.gg/EmeraldServers")
            
            await ctx.respond(embed=embed)
            
        except Exception as e:
            logger.error(f"Failed to check parser status: {e}")
            await ctx.respond("❌ Failed to retrieve parser status.", ephemeral=True)
    
    @parser.command(name="refresh", description="Manually refresh data for a server")
    @commands.has_permissions(administrator=True)
    @discord.option(
        name="server",
        description="Select a server",
        autocomplete=ServerAutocomplete.autocomplete_server_name
    )
    async def parser_refresh(self, ctx: discord.ApplicationContext, server: str = "default"):
        """Manually trigger a data refresh for a server"""
        try:
            guild_id = ctx.guild.id
            
            # Check if server exists in guild config
            guild_config = await self.bot.database.guilds.find_one({"guild_id": guild_id})
            if not guild_config:
                await ctx.respond("❌ This guild is not configured!", ephemeral=True)
                return
            
            # Find the server - now using server ID from autocomplete
            servers = guild_config.get('servers', [])
            server_found = False
            server_name = "Unknown"
            for srv in servers:
                if str(srv.get('_id')) == server:
                    server_found = True
                    server_name = srv.get('name', 'Unknown')
                    break
            
            if not server_found:
                await ctx.respond(f"❌ Server not found in this guild!", ephemeral=True)
                return
            
            # Defer response for potentially long operation
            await ctx.defer()
            
            # Trigger historical refresh if parser is available
            if hasattr(self.bot, 'historical_parser') and self.bot.historical_parser:
                try:
                    await self.bot.historical_parser.refresh_historical_data(guild_id, server)
                    
                    embed = discord.Embed(
                        title="🔄 Data Refresh Initiated",
                        description=f"Historical data refresh started for server **{server_name}**",
                        color=0x00FF00,
                        timestamp=datetime.now(timezone.utc)
                    )
                    
                    embed.add_field(
                        name="⏰ Duration",
                        value="This process may take several minutes",
                        inline=True
                    )
                    
                    embed.add_field(
                        name="📊 Data Updated",
                        value="• Player statistics\n• Kill/death records\n• Historical trends",
                        inline=True
                    )
                    
                    embed.set_footer(text="Powered by Discord.gg/EmeraldServers")
                    
                    await ctx.followup.send(embed=embed)
                    
                except Exception as e:
                    logger.error(f"Failed to refresh data: {e}")
                    await ctx.followup.send("❌ Failed to start data refresh. Please try again later.")
            else:
                await ctx.followup.send("❌ Historical parser is not available!")
                
        except Exception as e:
            logger.error(f"Failed to refresh parser data: {e}")
            await ctx.respond("❌ Failed to initiate data refresh.", ephemeral=True)
    
    @parser.command(name="stats", description="Show parser statistics")
    async def parser_stats(self, ctx: discord.ApplicationContext):
        """Display parser performance statistics"""
        try:
            guild_id = ctx.guild.id
            
            embed = discord.Embed(
                title="📊 Parser Statistics",
                description="Performance metrics for data parsers",
                color=0x9B59B6,
                timestamp=datetime.now(timezone.utc)
            )
            
            # Get recent parsing stats from database
            try:
                # Count recent killfeed entries (last 24 hours)
                recent_kills = await self.bot.database.killfeed.count_documents({
                    'guild_id': guild_id,
                    'timestamp': {'$gte': datetime.now(timezone.utc).replace(hour=0, minute=0, second=0)}
                })
                
                # Count total players tracked
                total_players = await self.bot.database.pvp_data.count_documents({
                    'guild_id': guild_id
                })
                
                # Count linked players
                linked_players = await self.bot.database.players.count_documents({
                    'guild_id': guild_id
                })
                
                embed.add_field(
                    name="📈 Today's Activity",
                    value=f"• Kills Parsed: **{recent_kills}**\n• Players Tracked: **{total_players}**\n• Linked Users: **{linked_players}**",
                    inline=True
                )
                
                # Parser uptime
                uptime_status = "🟢 Operational" if self.bot.scheduler.running else "🔴 Down"
                embed.add_field(
                    name="⚡ System Health",
                    value=f"• Parser Status: **{uptime_status}**\n• Database: **🟢 Connected**\n• Scheduler: **🟢 Active**",
                    inline=True
                )
                
            except Exception as e:
                logger.error(f"Failed to get parser stats from database: {e}")
                embed.add_field(
                    name="⚠️ Statistics",
                    value="Unable to retrieve detailed statistics",
                    inline=False
                )
            
            embed.set_thumbnail(url="attachment://main.png")
            embed.set_footer(text="Powered by Discord.gg/EmeraldServers")
            
            await ctx.respond(embed=embed)
            
        except Exception as e:
            logger.error(f"Failed to show parser stats: {e}")
            await ctx.respond("❌ Failed to retrieve parser statistics.", ephemeral=True)

def setup(bot):
    bot.add_cog(Parsers(bot))