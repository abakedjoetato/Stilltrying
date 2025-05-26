"""
Emerald's Killfeed - Core Commands (PHASE 1)
Basic bot information and utility commands
"""

import logging
from datetime import datetime, timezone
from typing import Optional

import discord
from discord.ext import commands
from bot.utils.embed_factory import EmbedFactory

logger = logging.getLogger(__name__)

class Core(commands.Cog):
    """
    CORE COMMANDS (FREE)
    - /info, /ping, /help, /status
    - Basic bot functionality
    """

    def __init__(self, bot):
        self.bot = bot

    @discord.slash_command(name="info", description="Get bot information")
    async def info(self, ctx: discord.ApplicationContext):
        """Display bot information"""
        try:
            embed = EmbedFactory.build(
                embed_type="core",
                title="🤖 Bot Information",
                description="Emerald's Killfeed - Advanced Deadside server management",
                data={
                    "bot_name": "Emerald's Killfeed",
                    "version": "2.6.1",
                    "guild_count": len(self.bot.guilds),
                    "user_count": len(self.bot.users),
                    "thumbnail_url": "attachment://main.png"
                }
            )

            if isinstance(embed, tuple):
                embed_obj, file_obj = embed
                if file_obj:
                    await ctx.respond(embed=embed_obj, file=file_obj)
                else:
                    await ctx.respond(embed=embed_obj)
            else:
                await ctx.respond(embed=embed)

        except Exception as e:
            logger.error(f"Failed to show bot info: {e}")
            await ctx.respond("❌ Failed to retrieve bot information.", ephemeral=True)

    @discord.slash_command(name="ping", description="Check bot latency")
    async def ping(self, ctx: discord.ApplicationContext):
        """Display bot latency"""
        try:
            latency = round(self.bot.latency * 1000)

            embed = EmbedFactory.build(
                embed_type="core",
                title="🏓 Pong!",
                description=f"Bot latency: **{latency}ms**",
                data={
                    "latency": latency,
                    "thumbnail_url": "attachment://main.png"
                }
            )

            if isinstance(embed, tuple):
                embed_obj, file_obj = embed
                if file_obj:
                    await ctx.respond(embed=embed_obj, file=file_obj)
                else:
                    await ctx.respond(embed=embed_obj)
            else:
                await ctx.respond(embed=embed)

        except Exception as e:
            logger.error(f"Failed to show ping: {e}")
            await ctx.respond("❌ Failed to check latency.", ephemeral=True)

    @discord.slash_command(name="help", description="Get help with bot commands")
    async def help(self, ctx: discord.ApplicationContext):
        """Display help information"""
        try:
            embed = EmbedFactory.build(
                embed_type="core",
                title="📚 Bot Help",
                description="Available commands and features",
                data={
                    "commands": [
                        "/info - Bot information",
                        "/ping - Check latency",
                        "/help - This help message",
                        "/status - Bot status"
                    ],
                    "thumbnail_url": "attachment://main.png"
                }
            )

            if isinstance(embed, tuple):
                embed_obj, file_obj = embed
                if file_obj:
                    await ctx.respond(embed=embed_obj, file=file_obj)
                else:
                    await ctx.respond(embed=embed_obj)
            else:
                await ctx.respond(embed=embed)

        except Exception as e:
            logger.error(f"Failed to show help: {e}")
            await ctx.respond("❌ Failed to retrieve help information.", ephemeral=True)

    @discord.slash_command(name="status", description="Check bot status")
    async def status(self, ctx: discord.ApplicationContext):
        """Display bot status"""
        try:
            uptime = datetime.now(timezone.utc) - self.bot.start_time if hasattr(self.bot, 'start_time') else None

            embed = EmbedFactory.build(
                embed_type="core",
                title="📊 Bot Status",
                description="Current bot operational status",
                data={
                    "status": "Online",
                    "guilds": len(self.bot.guilds),
                    "users": len(self.bot.users),
                    "uptime": str(uptime).split('.')[0] if uptime else "Unknown",
                    "thumbnail_url": "attachment://main.png"
                }
            )

            if isinstance(embed, tuple):
                embed_obj, file_obj = embed
                if file_obj:
                    await ctx.respond(embed=embed_obj, file=file_obj)
                else:
                    await ctx.respond(embed=embed_obj)
            else:
                await ctx.respond(embed=embed)

        except Exception as e:
            logger.error(f"Failed to show status: {e}")
            await ctx.respond("❌ Failed to retrieve status information.", ephemeral=True)

def setup(bot):
    bot.add_cog(Core(bot))