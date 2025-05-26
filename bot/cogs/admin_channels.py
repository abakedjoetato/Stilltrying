"""
Emerald's Killfeed - Admin Channel Management
Configure channels for various bot functions
"""

import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

import discord
from discord.ext import commands
from bot.utils.embed_factory import EmbedFactory

logger = logging.getLogger(__name__)

class AdminChannels(commands.Cog):
    """
    ADMIN CHANNEL MANAGEMENT
    - Configure killfeed channels
    - Set up notification channels
    - Manage channel permissions
    """

    def __init__(self, bot):
        self.bot = bot

    @discord.slash_command(name="channel_set", description="Set a channel for bot functions", default_member_permissions=discord.Permissions(administrator=True))
    async def channel_set(self, ctx: discord.ApplicationContext, 
                         channel_type: discord.Option(str, "Type of channel", 
                                                     choices=["killfeed", "notifications", "logs"]),
                         channel: discord.TextChannel,
                         server_id: str = "default"):
        """Set a channel for specific bot functions"""
        try:
            guild_id = ctx.guild.id

            # Update channel configuration
            success = await self.bot.db_manager.set_channel(guild_id, server_id, channel_type, channel.id)

            if success:
                embed = EmbedFactory.build(
                    title="⚙️ Channel Configured",
                    description=f"Successfully configured **{channel_type}** channel",
                    color=0x00FF00,
                    timestamp=datetime.now(timezone.utc)
                )

                embed.add_field(
                    name="📺 Channel",
                    value=channel.mention,
                    inline=True
                )

                embed.add_field(
                    name="🏷️ Type",
                    value=channel_type.title(),
                    inline=True
                )

                embed.add_field(
                    name="🖥️ Server",
                    value=server_id,
                    inline=True
                )

                await ctx.respond(embed=embed)
            else:
                await ctx.respond("❌ Failed to configure channel.", ephemeral=True)

        except Exception as e:
            logger.error(f"Failed to set channel: {e}")
            await ctx.respond("❌ Failed to configure channel.", ephemeral=True)

    @discord.slash_command(name="channel_list", description="List configured channels", default_member_permissions=discord.Permissions(administrator=True))
    async def channel_list(self, ctx: discord.ApplicationContext, 
                          server_id: str = "default"):
        """List all configured channels for a server"""
        try:
            guild_id = ctx.guild.id

            # Get server configuration
            server_config = await self.bot.db_manager.get_server_config(guild_id, server_id)

            if not server_config:
                embed = EmbedFactory.build(
                    title="📺 Channel Configuration",
                    description=f"No configuration found for server **{server_id}**",
                    color=0x808080,
                    timestamp=datetime.now(timezone.utc)
                )
                await ctx.respond(embed=embed)
                return

            embed = EmbedFactory.build(
                title="📺 Channel Configuration",
                description=f"Channel settings for server **{server_id}**",
                color=0x3498DB,
                timestamp=datetime.now(timezone.utc)
            )

            channels = server_config.get('channels', {})

            for channel_type, channel_id in channels.items():
                try:
                    channel = self.bot.get_channel(channel_id)
                    if channel:
                        embed.add_field(
                            name=f"📺 {channel_type.title()}",
                            value=channel.mention,
                            inline=True
                        )
                    else:
                        embed.add_field(
                            name=f"📺 {channel_type.title()}",
                            value=f"❌ Channel not found (ID: {channel_id})",
                            inline=True
                        )
                except:
                    embed.add_field(
                        name=f"📺 {channel_type.title()}",
                        value=f"❌ Invalid channel (ID: {channel_id})",
                        inline=True
                    )

            if not channels:
                embed.add_field(
                    name="ℹ️ No Channels Configured",
                    value="Use `/channel_set` to configure channels",
                    inline=False
                )

            await ctx.respond(embed=embed)

        except Exception as e:
            logger.error(f"Failed to list channels: {e}")
            await ctx.respond("❌ Failed to retrieve channel configuration.", ephemeral=True)

def setup(bot):
    bot.add_cog(AdminChannels(bot))