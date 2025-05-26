"""
Emerald's Killfeed - Bounty System
Place and claim bounties on players
"""

import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

import discord
from discord.ext import commands
from bot.utils.embed_factory import EmbedFactory

logger = logging.getLogger(__name__)

class Bounties(commands.Cog):
    """
    BOUNTIES (PREMIUM)
    - Place bounties on players
    - Claim bounty rewards
    - Track active bounties
    """

    def __init__(self, bot):
        self.bot = bot

    async def check_premium_server(self, guild_id: int) -> bool:
        """Check if guild has premium access for bounty features"""
        guild_doc = await self.bot.db_manager.get_guild(guild_id)
        if not guild_doc:
            return False

        servers = guild_doc.get('servers', [])
        for server_config in servers:
            server_id = server_config.get('server_id', server_config.get('_id', 'default'))
            if await self.bot.db_manager.is_premium_server(guild_id, server_id):
                return True

        return False

    @discord.slash_command(name="bounty_place", description="Place a bounty on a player")
    async def bounty_place(self, ctx: discord.ApplicationContext, 
                          target: str, amount: int, reason: str = "No reason provided"):
        """Place a bounty on a target player"""
        try:
            guild_id = ctx.guild.id
            discord_id = ctx.user.id

            # Check premium access
            if not await self.check_premium_server(guild_id):
                embed = EmbedFactory.build(
                    title="🔒 Premium Feature",
                    description="Bounty system requires premium subscription!",
                    color=0xFF6B6B
                )
                await ctx.respond(embed=embed, ephemeral=True)
                return

            # Validate amount
            if amount <= 0:
                await ctx.respond("❌ Bounty amount must be positive!", ephemeral=True)
                return

            if amount > 10000:
                await ctx.respond("❌ Maximum bounty amount is $10,000!", ephemeral=True)
                return

            # Check wallet balance
            wallet = await self.bot.db_manager.get_wallet(guild_id, discord_id)
            if wallet['balance'] < amount:
                await ctx.respond(
                    f"❌ Insufficient funds! You have **${wallet['balance']:,}** but need **${amount:,}**",
                    ephemeral=True
                )
                return

            # Place bounty
            success = await self.bot.db_manager.place_bounty(guild_id, discord_id, target, amount, reason)

            if success:
                # Deduct from wallet
                await self.bot.db_manager.update_wallet(guild_id, discord_id, -amount, "bounty_placed")

                embed = EmbedFactory.build(
                    title="🎯 Bounty Placed",
                    description=f"Bounty successfully placed on **{target}**",
                    color=0xFF4500,
                    timestamp=datetime.now(timezone.utc)
                )

                embed.add_field(
                    name="💰 Amount",
                    value=f"${amount:,}",
                    inline=True
                )

                embed.add_field(
                    name="📝 Reason",
                    value=reason,
                    inline=True
                )

                embed.add_field(
                    name="👤 Placed by",
                    value=ctx.user.mention,
                    inline=True
                )

                await ctx.respond(embed=embed)
            else:
                await ctx.respond("❌ Failed to place bounty. Player may already have an active bounty.", ephemeral=True)

        except Exception as e:
            logger.error(f"Failed to place bounty: {e}")
            await ctx.respond("❌ Failed to place bounty.", ephemeral=True)

    @discord.slash_command(name="bounty_list", description="View active bounties")
    async def bounty_list(self, ctx: discord.ApplicationContext):
        """List all active bounties"""
        try:
            guild_id = ctx.guild.id

            # Check premium access
            if not await self.check_premium_server(guild_id):
                embed = EmbedFactory.build(
                    title="🔒 Premium Feature",
                    description="Bounty system requires premium subscription!",
                    color=0xFF6B6B
                )
                await ctx.respond(embed=embed, ephemeral=True)
                return

            # Get active bounties
            bounties = await self.bot.db_manager.get_active_bounties(guild_id)

            if not bounties:
                embed = EmbedFactory.build(
                    title="🎯 Active Bounties",
                    description="No active bounties at this time.",
                    color=0x808080,
                    timestamp=datetime.now(timezone.utc)
                )
                await ctx.respond(embed=embed)
                return

            embed = EmbedFactory.build(
                title="🎯 Active Bounties",
                description="Current bounties available for claiming",
                color=0xFF4500,
                timestamp=datetime.now(timezone.utc)
            )

            for i, bounty in enumerate(bounties[:10], 1):  # Top 10
                embed.add_field(
                    name=f"{i}. {bounty['target']}",
                    value=f"💰 **${bounty['amount']:,}**\n📝 {bounty['reason']}\n👤 By: <@{bounty['placed_by']}>",
                    inline=True
                )

            await ctx.respond(embed=embed)

        except Exception as e:
            logger.error(f"Failed to list bounties: {e}")
            await ctx.respond("❌ Failed to retrieve bounty list.", ephemeral=True)

def setup(bot):
    bot.add_cog(Bounties(bot))